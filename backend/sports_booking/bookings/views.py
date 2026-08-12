from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db import transaction, IntegrityError
from datetime import datetime, timedelta, time as dt_time
import logging

from .models import Booking, SlotLock, SlotWaitlist
from .serializers import (
    BookingSerializer,
    SlotLockSerializer,
    SlotWaitlistSerializer,
)
from .tasks import (
    send_booking_confirmation_email,
    send_booking_confirmation_sms,
    notify_waitlisted_users,
)
from clubs.models import Sport

logger = logging.getLogger(__name__)

MAX_ADVANCE_BOOKING_DAYS = 15
STALE_PENDING_MINUTES = 15


def _slot_datetime(date, time_str):
    """Combine a date with an 'HH:MM:SS' string into a tz-aware datetime."""
    hour, minute, second = (int(p) for p in time_str.split(':'))
    return timezone.make_aware(datetime.combine(date, dt_time(hour, minute, second)))


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # select_related('payment') so BookingSerializer.get_payment_method
        # never issues an extra query per row (fixes N+1 in list views).
        base = Booking.objects.select_related('user', 'club', 'sport', 'payment')
        if self.request.user.is_staff:
            return base.all()
        return base.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a club, sport, and date."""
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

        max_allowed_date = timezone.now().date() + timedelta(days=MAX_ADVANCE_BOOKING_DAYS)
        if date > max_allowed_date:
            return Response(
                {'error': f'Slots are only available up to {MAX_ADVANCE_BOOKING_DAYS} days in advance (latest: {max_allowed_date}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Auto-cleanup: expire stale locks and their pending bookings.
        expired_locks = list(SlotLock.objects.filter(
            club_id=club_id, sport_id=sport_id, date=date,
            expires_at__lt=timezone.now(), is_converted=False
        ))
        for lock in expired_locks:
            Booking.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                start_time=lock.start_time, status='pending'
            ).update(status='cancelled')
        SlotLock.objects.filter(id__in=[l.id for l in expired_locks]).delete()

        try:
            sport = Sport.objects.select_related('club').get(id=sport_id)
        except Sport.DoesNotExist:
            return Response({'error': 'Sport not found'}, status=status.HTTP_404_NOT_FOUND)

        if not sport.is_active:
            return Response(
                {'error': 'This sport is currently not available for booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        club = sport.club
        price = sport.price_per_hour

        # Fetch the whole day's bookings and locks ONCE instead of per-slot
        # (fixes N+1: was up to 32 queries for this endpoint, now 2).
        booked_start_times = set(
            Booking.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                status__in=['confirmed', 'pending']
            ).values_list('start_time', flat=True)
        )
        locked_start_times = set(
            SlotLock.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                expires_at__gt=timezone.now(), is_converted=False
            ).exclude(user=request.user).values_list('start_time', flat=True)
        )

        # Clamp generated slots to the club's actual operating hours instead
        # of a hardcoded 6am-10pm window.
        start_hour = max(6, club.opening_time.hour)
        end_hour = min(22, club.closing_time.hour)

        now = timezone.now()
        slots = []
        for hour in range(start_hour, end_hour):
            start_time_str = f"{hour:02d}:00:00"
            end_time_str = f"{hour + 1:02d}:00:00"
            start_time = dt_time(hour, 0, 0)

            is_past = _slot_datetime(date, start_time_str) <= now
            is_booked = start_time in booked_start_times
            is_locked = start_time in locked_start_times

            slots.append({
                'start_time': start_time_str,
                'end_time': end_time_str,
                'is_booked': is_booked or is_past,
                'is_locked': is_locked,
                'is_past': is_past,
                'price': float(price)
            })

        return Response(slots)

    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'))
    @action(detail=False, methods=['post'])
    def lock_slot(self, request):
        """Lock a slot for SLOT_LOCK_DURATION seconds while the user pays."""
        club_id = request.data.get('club')
        sport_id = request.data.get('sport')
        date_str = request.data.get('date')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not all([club_id, sport_id, date_str, start_time, end_time]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot_dt = _slot_datetime(date, start_time)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid start_time format'}, status=status.HTTP_400_BAD_REQUEST)

        if slot_dt <= timezone.now():
            return Response({'error': 'Cannot book a slot that has already passed.'}, status=status.HTTP_400_BAD_REQUEST)

        max_date = timezone.now().date() + timedelta(days=MAX_ADVANCE_BOOKING_DAYS)
        if date > max_date:
            return Response(
                {'error': f'Bookings can only be made up to {MAX_ADVANCE_BOOKING_DAYS} days in advance (latest: {max_date}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sport = Sport.objects.get(id=sport_id)
        except Sport.DoesNotExist:
            return Response({'error': 'Sport not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not sport.is_active:
            return Response({'error': 'This sport is currently not available for booking.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            existing_booking = Booking.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date, start_time=start_time,
                status__in=['confirmed', 'pending']
            ).exists()
            if existing_booking:
                return Response({'error': 'Slot is already booked'}, status=status.HTTP_400_BAD_REQUEST)

            active_lock = SlotLock.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date, start_time=start_time,
                expires_at__gt=timezone.now(), is_converted=False
            ).exclude(user=request.user).exists()

            if active_lock:
                waitlist_entry, created = SlotWaitlist.objects.get_or_create(
                    user=request.user, club_id=club_id, sport_id=sport_id,
                    date=date, start_time=start_time, end_time=end_time,
                    defaults={'notified': False}
                )
                if created:
                    logger.info(f"User {request.user.username} added to waitlist")
                return Response(
                    {'error': 'Slot is currently locked by another user. You have been added to the waitlist.',
                     'waitlisted': True},
                    status=status.HTTP_409_CONFLICT
                )

            # Remove this user from the waitlist for this slot if present.
            SlotWaitlist.objects.filter(
                user=request.user, club_id=club_id, sport_id=sport_id,
                date=date, start_time=start_time
            ).delete()

            # Clean up ANY expired lock on this exact slot — not just the
            # requesting user's — otherwise the unique_together constraint
            # below can raise an unhandled IntegrityError. This was the
            # critical race-condition bug in the original code.
            SlotLock.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                start_time=start_time, end_time=end_time,
                expires_at__lt=timezone.now(), is_converted=False
            ).delete()

            # Also drop any of this user's own (non-expired) lock on the
            # same slot, e.g. a retry after a failed create().
            SlotLock.objects.filter(
                club_id=club_id, sport_id=sport_id, date=date,
                start_time=start_time, user=request.user, is_converted=False
            ).delete()

            try:
                lock = SlotLock.objects.create(
                    club_id=club_id, sport_id=sport_id, date=date,
                    start_time=start_time, end_time=end_time, user=request.user
                )
            except IntegrityError:
                # Someone else grabbed this slot in the tiny window between
                # our cleanup above and this insert. Fail gracefully instead
                # of a 500.
                return Response(
                    {'error': 'This slot was just taken by another user. Please pick a different slot.'},
                    status=status.HTTP_409_CONFLICT
                )

        serializer = SlotLockSerializer(lock)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def waitlist(self, request):
        """Get the current user's waitlisted slots."""
        waitlist = SlotWaitlist.objects.filter(
            user=request.user
        ).select_related('club', 'sport').order_by('-created_at')
        serializer = SlotWaitlistSerializer(waitlist, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='waitlist/(?P<waitlist_id>[^/.]+)')
    def remove_from_waitlist(self, request, waitlist_id=None):
        """Remove the user from the waitlist for a specific slot."""
        try:
            waitlist_entry = SlotWaitlist.objects.get(id=waitlist_id, user=request.user)
            waitlist_entry.delete()
            return Response({'message': 'Removed from waitlist'}, status=status.HTTP_200_OK)
        except SlotWaitlist.DoesNotExist:
            return Response({'error': 'Waitlist entry not found'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """Create a pending booking from a locked slot."""
        lock_id = request.data.get('lock_id')
        if not lock_id:
            return Response({'error': 'lock_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Lock the row for the duration of this transaction so a
                # concurrent/retried request can't create a second booking
                # off the same SlotLock (previously no locking at all).
                lock = SlotLock.objects.select_for_update().select_related('club', 'sport').get(
                    id=lock_id, user=request.user
                )

                if lock.is_expired():
                    lock.delete()
                    return Response(
                        {'error': 'Slot lock has expired. Please select the slot again.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if lock.is_converted:
                    return Response({'error': 'This lock has already been used'}, status=status.HTTP_400_BAD_REQUEST)

                if not lock.sport.is_active:
                    return Response(
                        {'error': 'This sport is no longer available for booking.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                booking = Booking.objects.create(
                    user=request.user,
                    club=lock.club,
                    sport=lock.sport,
                    date=lock.date,
                    start_time=lock.start_time,
                    end_time=lock.end_time,
                    # Price ALWAYS comes from the server-side sport record,
                    # never from the client. The original code trusted
                    # request.data['amount'] — a critical pricing exploit.
                    amount=lock.sport.price_per_hour,
                    lock=lock,
                    status='pending'
                )

            serializer = self.get_serializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except SlotLock.DoesNotExist:
            return Response({'error': 'Invalid lock_id or lock expired'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking with reason, enforce 24hr policy, process refund if paid."""
        booking = self.get_object()

        if booking.user != request.user and not request.user.is_staff:
            return Response({'error': 'You can only cancel your own bookings'}, status=status.HTTP_403_FORBIDDEN)

        if booking.status in ('cancelled', 'refunded'):
            return Response({'error': f'Booking is already {booking.status}'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status == 'completed':
            return Response({'error': 'Cannot cancel a completed booking'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status == 'confirmed' and not request.user.is_staff:
            booking_dt = timezone.make_aware(datetime.combine(booking.date, booking.start_time))
            hours_until = (booking_dt - timezone.now()).total_seconds() / 3600
            if hours_until < 0:
                return Response({'error': 'This booking has already passed.'}, status=status.HTTP_400_BAD_REQUEST)
            if hours_until < 24:
                return Response(
                    {'error': 'Cancellation is not allowed within 24 hours of the booking time.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        reason = request.data.get('reason', '').strip()
        if not reason and not request.user.is_staff:
            return Response({'error': 'Cancellation reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        was_confirmed = booking.status == 'confirmed'

        with transaction.atomic():
            booking.cancellation_reason = reason

            if was_confirmed:
                # Only Payment.DoesNotExist is expected here (unpaid/dev
                # booking marked confirmed without a payment record). Any
                # other exception is a real bug and must NOT be silently
                # swallowed — that was hiding refund failures.
                try:
                    payment = booking.payment
                    if payment.status == 'completed':
                        payment.mark_refunded()
                        booking.status = 'refunded'
                    else:
                        booking.status = 'cancelled'
                except Booking.payment.RelatedObjectDoesNotExist:
                    booking.status = 'cancelled'
                except Exception:
                    logger.exception(f"Refund processing failed for booking {booking.id}")
                    raise
            else:
                booking.status = 'cancelled'

            booking.save()

            SlotLock.objects.filter(
                club=booking.club, sport=booking.sport,
                date=booking.date, start_time=booking.start_time,
                is_converted=False
            ).delete()

        logger.info(f"Booking {booking.id} {booking.status} by {request.user.username}. Reason: {reason}")

        # Let anyone waitlisted for this slot know it's free again.
        notify_waitlisted_users.delay(
            str(booking.club_id), str(booking.sport_id),
            booking.date.strftime('%Y-%m-%d'),
            str(booking.start_time), str(booking.end_time)
        )

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
        """Admin action: release all expired locks and cancel their pending bookings."""
        expired_locks = list(SlotLock.objects.filter(expires_at__lt=timezone.now(), is_converted=False))
        cancelled = 0
        for lock in expired_locks:
            cancelled += Booking.objects.filter(
                club=lock.club, sport=lock.sport, date=lock.date,
                start_time=lock.start_time, status='pending'
            ).update(status='cancelled')
        SlotLock.objects.filter(id__in=[l.id for l in expired_locks]).delete()

        cutoff = timezone.now() - timedelta(minutes=STALE_PENDING_MINUTES)
        stale = Booking.objects.filter(status='pending', created_at__lt=cutoff)
        stale_count = stale.count()
        stale.update(status='cancelled')

        total_cancelled = cancelled + stale_count
        return Response({
            'message': f'Released {len(expired_locks)} expired locks, cancelled {total_cancelled} pending bookings',
            'released_locks': len(expired_locks),
            'cancelled_bookings': total_cancelled
        })

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming bookings for the user."""
        today = timezone.now().date()
        upcoming = self.get_queryset().filter(
            date__gte=today, status__in=['confirmed', 'pending']
        ).order_by('date', 'start_time')
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get past bookings for the user."""
        today = timezone.now().date()
        history = self.get_queryset().filter(date__lt=today).order_by('-date', '-start_time')
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)