from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from payments.models import Payment
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up expired payments and QR codes'
    
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
            help='Hours past expiration to clean up (default: 1)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours = options['hours']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        expired_payments = Payment.objects.filter(
            expires_at__lt=cutoff_time,
            status='pending'
        )
        
        self.stdout.write(f"Found {expired_payments.count()} expired payments to clean up")
        
        if not dry_run:
            count = 0
            for payment in expired_payments:
                if payment.qr_code:
                    try:
                        payment.qr_code.delete()
                        self.stdout.write(f"Deleted QR code for payment {payment.transaction_id}")
                    except Exception as e:
                        logger.error(f"Failed to delete QR code for {payment.transaction_id}: {e}")
                
                payment.status = 'expired'
                payment.save()
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {count} expired payments')
            )
        else:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes made')
            )