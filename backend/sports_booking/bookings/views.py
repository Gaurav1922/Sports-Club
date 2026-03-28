from rest_framework import status, viewsets
from rest_framework.decorators import action
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
from .tasks import send_booking_confirmation_email, send_booking_confirmation_sms
from clubs.models import Sport

logger = logging.getLogger(__name__)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    # FIX 1: Removed duplicate permission_classes line — second one was
    # overriding the first, locking ALL users out (only admins could access bookings)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.select_related('user', 'club', 'sport', 'payment').all()
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('club', 'sport', 'payment')

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

        # Reject dates beyond 15 days from today
        max_allowed_date = timezone.now().date() + timedelta(days=15)
        if date > max_allowed_date:
            return Response(
                {'error': f'Slots are only available up to 15 days in advance (latest: {max_allowed_date}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Auto-cleanup: expire stale locks and pending bookings (since Celery may not be running)
        expired_locks = SlotLock.objects.filter(
            club_id=club_id, sport_id=sport_id, date=date,
            expires_at__lt=timezone.now(), is_converted=False
        )
        # Cancel pending bookings whose lock has expired
        for lock in expired_locks:
            Booking.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                start_time=lock.start_time, status='pending'
            ).update(status='cancelled')
        expired_locks.delete()

        # Get sport price and check active status
        try:
            sport = Sport.objects.get(id=sport_id)
            if not sport.is_active:
                return Response(
                    {'error': 'This sport is currently not available for booking'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            price = sport.price_per_hour
        except Sport.DoesNotExist:
            return Response(
                {'error': 'Sport not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate hourly slots from 6 AM to 10 PM
        now = timezone.now()
        slots = []
        for hour in range(6, 22):
            start_time = f"{hour:02d}:00:00"
            end_time = f"{hour + 1:02d}:00:00"

            # Check if slot is in the past
            slot_datetime = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.strptime(start_time, '%H:%M:%S').time())
            )
            is_past = slot_datetime <= now

            is_booked = Booking.objects.filter(
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time,
                status__in=['confirmed', 'pending']
            ).exists()

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
                'is_booked': is_booked or is_past,
                'is_locked': active_lock,
                'is_past': is_past,
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

            # Reject past slots
            slot_datetime = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.strptime(start_time, '%H:%M:%S').time())
            )
            if slot_datetime <= timezone.now():
                return Response(
                    {'error': 'Cannot book a slot that has already passed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reject bookings more than 15 days in advance
            max_date = timezone.now().date() + timedelta(days=15)
            if date > max_date:
                return Response(
                    {'error': f'Bookings can only be made up to 15 days in advance (latest: {max_date}).'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check sport is active
            try:
                sport = Sport.objects.get(id=sport_id)
                if not sport.is_active:
                    return Response(
                        {'error': 'This sport is currently not available for booking.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Sport.DoesNotExist:
                return Response(
                    {'error': 'Sport not found.'},
                    status=status.HTTP_404_NOT_FOUND
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
                    logger.info(f"User {request.user.username} added to waitlist")

                return Response(
                    {
                        'error': 'Slot is currently locked by another user. You have been added to the waitlist.',
                        'waitlisted': True
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # Remove user from waitlist if they previously waitlisted this slot
            SlotWaitlist.objects.filter(
                user=request.user,
                club_id=club_id,
                sport_id=sport_id,
                date=date,
                start_time=start_time
            ).delete()

            # Clean up expired locks for this user
            SlotLock.objects.filter(
                user=request.user,
                expires_at__lt=timezone.now(),
                is_converted=False
            ).delete()

            # Delete existing lock by this user on same slot
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

    @action(detail=False, methods=['get'])
    def waitlist(self, request):
        """Get user's waitlisted slots"""
        waitlist = SlotWaitlist.objects.filter(
            user=request.user
        ).select_related('club', 'sport').order_by('-created_at')
        serializer = SlotWaitlistSerializer(waitlist, many=True)
        return Response(serializer.data)

    # FIX 2: Changed url_path to use just waitlist_id (simpler, matches frontend call)
    @action(detail=False, methods=['delete'], url_path='waitlist/(?P<waitlist_id>[^/.]+)')
    def remove_from_waitlist(self, request, waitlist_id=None):
        """Remove user from waitlist for a specific slot"""
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
        """Cancel a booking with reason, enforce 24hr policy, process refund if paid"""
        booking = self.get_object()

        if booking.user != request.user and not request.user.is_staff:
            return Response({'error': 'You can only cancel your own bookings'}, status=status.HTTP_403_FORBIDDEN)

        if booking.status in ('cancelled', 'refunded'):
            return Response({'error': f'Booking is already {booking.status}'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status == 'completed':
            return Response({'error': 'Cannot cancel a completed booking'}, status=status.HTTP_400_BAD_REQUEST)

        # 24-hour cancellation policy (only for confirmed bookings, not admin)
        if booking.status == 'confirmed' and not request.user.is_staff:
            booking_datetime = timezone.datetime.combine(booking.date, booking.start_time)
            booking_datetime = timezone.make_aware(booking_datetime)
            hours_until = (booking_datetime - timezone.now()).total_seconds() / 3600
            if hours_until < 0:
                return Response({'error': 'This booking has already passed.'}, status=status.HTTP_400_BAD_REQUEST)
            if hours_until < 24:
                return Response(
                    {'error': 'Cancellation is not allowed within 24 hours of the booking time.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Get cancellation reason
        reason = request.data.get('reason', '').strip()
        if not reason and not request.user.is_staff:
            return Response({'error': 'Cancellation reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        was_confirmed = booking.status == 'confirmed'

        with transaction.atomic():
            # Store reason in booking metadata if field exists, else log it
            if hasattr(booking, 'cancellation_reason'):
                booking.cancellation_reason = reason

            if was_confirmed:
                try:
                    payment = booking.payment
                    if payment and payment.status == 'completed':
                        payment.status = 'refunded'
                        payment.save(update_fields=['status'])
                        booking.status = 'refunded'
                    else:
                        booking.status = 'cancelled'
                except Exception:
                    booking.status = 'cancelled'
            else:
                booking.status = 'cancelled'

            booking.save()

            # Release slot lock
            SlotLock.objects.filter(
                club=booking.club, sport=booking.sport,
                date=booking.date, start_time=booking.start_time,
                is_converted=False
            ).delete()

        logger.info(f"Booking {booking.id} {booking.status} by {request.user.username}. Reason: {reason}")

        msg = (
            'Booking cancelled. Refund will be processed within 5-7 business days.'
            if booking.status == 'refunded'
            else 'Booking cancelled. Slot is now available for others.'
        )

        return Response({
            'message': msg,
            'booking_id': str(booking.id),
            'status': booking.status,
            'refund_amount': float(booking.amount) if booking.status == 'refunded' else 0
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def release_expired_slots(self, request):
        """Admin action: release all expired locks and cancel their pending bookings"""
        from django.utils import timezone as tz
        expired_locks = SlotLock.objects.filter(
            expires_at__lt=tz.now(),
            is_converted=False
        )
        released = 0
        cancelled = 0
        for lock in expired_locks:
            count, _ = Booking.objects.filter(
                club=lock.club,
                sport=lock.sport,
                date=lock.date,
                start_time=lock.start_time,
                status='pending'
            ).update(status='cancelled'), None
            cancelled += count[0] if isinstance(count, tuple) else count
            released += 1
        expired_locks.delete()

        # Also cancel pending bookings older than 15 minutes with no lock
        cutoff = tz.now() - timedelta(minutes=15)
        stale = Booking.objects.filter(
            status='pending',
            created_at__lt=cutoff
        )
        stale_count = stale.count()
        stale.update(status='cancelled')

        return Response({
            'message': f'Released {released} expired locks, cancelled {cancelled + stale_count} pending bookings',
            'released_locks': released,
            'cancelled_bookings': cancelled + stale_count
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
        # FIX 3: Removed unreachable dead code (try/except after return statement)
        history = self.get_queryset().filter(
            date__lt=today
        ).order_by('-date', '-start_time')
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)