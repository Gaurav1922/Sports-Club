from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import logging

from .models import Booking, SlotLock, SlotWaitlist
from .serializers import (
    BookingSerializer, 
    SlotLockSerializer, 
    SlotWaitlistSerializer,
)
from .tasks import send_booking_confirmation_email,send_booking_confirmation_sms
from clubs.models import Sport

logger = logging.getLogger(__name__)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.select_related('user', 'club', 'sport').all()
        return Booking.objects.filter(user=self.request.user).select_related('club', 'sport')
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a club, sport, and date"""
        club_id = request.query_params.get('club')
        sport_id = request.query_params.get('sport')
        date_str = request.query_params.get('date')
        
        if not all([club_id, sport_id, date_str]):
            return Response(
                {'error': 'club, sport, and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get sport price
        try:
            sport = Sport.objects.get(id=sport_id)
            price = sport.price_per_hour
        except Sport.DoesNotExist:
            return Response(
                {'error': 'Sport not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate hourly slots from 6 AM to 10 PM
        slots = []
        for hour in range(6, 22):
            start_time = f"{hour:02d}:00:00"
            end_time = f"{hour+1:02d}:00:00"
            
            # Check if slot is booked
            is_booked = Booking.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            # Check if slot is locked by another user
            active_lock = SlotLock.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                expires_at__gt=timezone.now(),
                is_converted=False
            ).exclude(user=request.user).exists()
            
            slots.append({
                'start_time': start_time,
                'end_time': end_time,
                'is_booked': is_booked,
                'is_locked': active_lock,
                'price': float(price)
            })
        
        return Response(slots)
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'])
    def lock_slot(self, request):
        """Lock a slot for 10 minutes while user completes payment"""
        with transaction.atomic():
            club_id = request.data.get('club')
            sport_id = request.data.get('sport')
            date_str = request.data.get('date')
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            
            if not all([club_id, sport_id, date_str, start_time, end_time]):
                return Response(
                    {'error': 'All fields are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if slot is already booked
            existing_booking = Booking.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if existing_booking:
                return Response(
                    {'error': 'Slot is already booked'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if slot is locked by another user
            active_lock = SlotLock.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                expires_at__gt=timezone.now(),
                is_converted=False
            ).exclude(user=request.user).exists()
            
            if active_lock:
                # Add user ro waitlist
                from .models import SlotWaitlist

                waitlist_entry, created = SlotWaitlist.objects.get_or_create(
                    user=request.user,
                    club_id=club_id,
                    sport_id=sport_id,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={'notified': False}
                )

                if created:
                    logger.info(f"User {request.user.username} added to waitlist for slot")

                return Response(
                    {
                        'error': 'Slot is currently locked by another user. You have been added to the waitlist and will be notified if it becomes available.',
                        'waitlisted': True
                     },
                    status=status.HTTP_409_CONFLICT
                )
            
            # check if user was on waitlist and remove them
            from .models import SlotWaitlist
            SlotWaitlist.objects.filter(
                user=request.user,
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time
            ).delete()
            
            # Delete any expired locks for this user
            SlotLock.objects.filter(
                user=request.user,
                expires_at__lt=timezone.now(),
                is_converted=False
            ).delete()
            
            # Delete existing lock for this user on same slot (if any)
            SlotLock.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                user=request.user,
                is_converted=False
            ).delete()
            
            # Create new lock
            lock = SlotLock.objects.create(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                user=request.user
            )
            
            serializer = SlotLockSerializer(lock)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['GET'])
    def waitlist(self, request):
        # Get user's waitlisted slots
        waitlist = SlotWaitlist.objects.filter(
            user=request.user
        ).select_related('club', 'sport').order_by('-created_at')

        serializer = SlotWaitlistSerializer(waitlist, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], url_path='waitlist/(?P<waitlist_id>[^/.]+)')
    def remove_from_waitlist(self, request, pk=None, waitlist_id=None):
        # Remove user from waitlist for specific slot
        try:
            waitlist_entry = SlotWaitlist.objects.get(
                id=waitlist_id,
                user=request.user
            )
            waitlist_entry.delete()
            return Response({'message': 'Removed from waitlist'}, status=status.HTTP_200_OK)
        except SlotWaitlist.DoesNotExist:
            return Response(
                {'error': 'Waitlist entry not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def create(self, request, *args, **kwargs):
        """Create booking with locked slot"""
        lock_id = request.data.get('lock_id')
        
        if not lock_id:
            return Response(
                {'error': 'lock_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lock = SlotLock.objects.select_related('club', 'sport').get(
                id=lock_id,
                user=request.user
            )
            
            if lock.is_expired():
                lock.delete()
                return Response(
                    {'error': 'Slot lock has expired. Please select the slot again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if lock.is_converted:
                return Response(
                    {'error': 'This lock has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create booking
            with transaction.atomic():
                booking = Booking.objects.create(
                    user=request.user,
                    club=lock.club,
                    sport=lock.sport,
                    date=lock.date,
                    start_time=lock.start_time,
                    end_time=lock.end_time,
                    amount=request.data.get('amount', lock.sport.price_per_hour),
                    lock=lock,
                    status='pending'
                )
                
                serializer = self.get_serializer(booking)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except SlotLock.DoesNotExist:
            return Response(
                {'error': 'Invalid lock_id or lock expired'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only cancel your own bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status == 'cancelled':
            return Response(
                {'error': 'Booking is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if booking.status == 'completed':
            return Response(
                {'error': 'Cannot cancel completed bookings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        logger.info(f"Booking {booking.id} cancelled by user {request.user.username}")
        
        return Response({
            'message': 'Booking cancelled successfully',
            'booking_id': booking.id
        })
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings for the user"""
        today = timezone.now().date()
        upcoming = self.get_queryset().filter(
            date__gte=today,
            status__in=['confirmed', 'pending']
        ).order_by('date', 'start_time')
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get past bookings for the user"""
        today = timezone.now().date()
        history = self.get_queryset().filter(
            date__lt=today
        ).order_by('-date', '-start_time')
        
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

    """# Create: bookings/views.py
    @action(detail=False, methods=['GET'])
    @permission_classes([IsAdminUser])
    def waitlist_analytics(self, request):
        from django.db.models import Count, Avg
        from datetime import timedelta
        from django.utils import calculate_waitlist_conversion

    
        stats = {
            'total_waitlisted': SlotWaitlist.objects.count(),
            'notified_today': SlotWaitlist.objects.filter(
                notified=True,
                created_at__date=timezone.now().date()
            ).count(),
            'most_popular_slots': SlotWaitlist.objects.values(
                'club__name', 'sport__name', 'start_time'
            ).annotate(
            count=Count('id')
            ).order_by('-count')[:5],
            'conversion_rate': calculate_waitlist_conversion(),
        }
        return Response(stats)"""