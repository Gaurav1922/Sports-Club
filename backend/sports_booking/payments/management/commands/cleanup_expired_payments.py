from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Mark stale pending payments as failed and cancel their bookings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='Hours since creation after which a pending payment is considered stale (default: 1)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']

        cutoff_time = timezone.now() - timedelta(hours=hours)
        expired_payments = Payment.objects.select_related('booking').filter(
            created_at__lt=cutoff_time,
            status='pending',
        )

        self.stdout.write(f"Found {expired_payments.count()} expired payments to clean up")

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))
            return

        count = 0
        for payment in expired_payments:
            with transaction.atomic():
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.failure_reason = 'Payment not completed within the allowed window'
                payment.save(update_fields=['status', 'failed_at', 'failure_reason'])

                booking = payment.booking
                if booking.status == 'pending':
                    booking.status = 'cancelled'
                    booking.cancellation_reason = 'Payment timed out'
                    booking.cancelled_at = timezone.now()
                    booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_at', 'updated_at'])
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned up {count} expired payments'))