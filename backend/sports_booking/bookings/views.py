from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import Booking
from .serializers import BookingSerializer, CreateBookingSerializer
from payments.models import Payment
import uuid
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            'club', 'time_slot'
        )
    
    def create(self, request):
        serializer = CreateBookingSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                club = serializer.validated_data['club']
                time_slot = serializer.validated_data['time_slot']

                # Double-check availability
                time_slot.refresh_from_db()
                if not time_slot.is_bookable:
                    return Response({
                        'error': 'Time slot is no longer available'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
                # Calculate total amount
                total_amount = time_slot.price

                # Create booking
                booking = serializer.save(
                    user=request.user,
                    total_amount=total_amount
                )

                # update time slot
                time_slot.current_bookings += 1
                if time_slot.current_bookings >= time_slot.max_capacity:
                    time_slot.is_available = False
                time_slot.save()

                logger.info(f"Booking created: {booking.id} for user {request.user.id}")

                return Response(
                    BookingSerializer(booking).data,
                    status=status.HTTP_201_CREATED
                )
            
        print("Incoming data:", request.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming_bookings = self.get_queryset().filter(
            time_slot__date__gte = timezone.now().date(),
            status__in = ['pending', 'confirmed']
        ).order_by('time_slot__date', 'time_slot__start_time')

        serializer = self.get_serializer(upcoming_bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        history_bookings = self.get_queryset().filter(
            status__in=['completed', 'cancelled', 'no_show']
        ).order_by('-booking_date')

        serializer = self.get_serializer(history_bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        cancellation_reason = request.data.get('reason', '')

        try:
            with transaction.atomic():
                booking.cancel_booking(cancellation_reason)

                # if payment was completed, infitiate refund
                if hasattr(booking, 'payment') and booking.payment.status == 'completed':
                    from payments.tasks import process_payment_refund
                    process_payment_refund.delay(booking.payment.id)
                
                logger.info(f"Booking cancelled: {booking.id} by user {request.user.id}")

                return Response({
                    'message': 'Booking cancelled successfully'
                }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    

