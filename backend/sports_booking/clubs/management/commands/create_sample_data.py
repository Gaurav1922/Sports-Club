from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, time, timedelta
from clubs.models import SportsClub, TimeSlot
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample sports clubs and time slots'
    
    def handle(self, *args, **options):
        # Create sample clubs
        clubs_data = [
            {
                'name': 'Elite Sports Complex',
                'description': 'Premium sports facility with state-of-the-art equipment and professional coaching.',
                'address': '123 Sports Avenue, MG Road, Bengaluru, Karnataka 560001',
                'latitude': 12.9716,
                'longitude': 77.5946,
                'sports_available': ['football', 'basketball', 'tennis', 'swimming'],
                'contact_number': '+919876543210',
                'email': 'info@elitesports.com',
                'rating': 4.8,
                'images': ['/api/placeholder/400/300'],
                'price_per_hour': Decimal('500.00'),
                'facilities': ['Parking', 'Changing Room', 'Cafeteria', 'Pro Shop'],
                'amenities': ['Air Conditioning', 'WiFi', 'First Aid', 'Equipment Rental'],
                'opening_time': time(6, 0),
                'closing_time': time(22, 0),
                'cancellation_policy': '24 hours advance notice required for cancellation.',
                'advance_booking_days': 7,
            },
            {
                'name': 'Champions Arena',
                'description': 'Multi-sport facility perfect for recreational and competitive play.',
                'address': '456 Victory Road, Koramangala, Bengaluru, Karnataka 560034',
                'latitude': 12.9279,
                'longitude': 77.6271,
                'sports_available': ['cricket', 'badminton', 'table_tennis', 'volleyball'],
                'contact_number': '+919876543211',
                'email': 'contact@championsarena.com',
                'rating': 4.6,
                'images': ['/api/placeholder/400/300'],
                'price_per_hour': Decimal('400.00'),
                'facilities': ['Parking', 'Changing Room', 'Equipment Rental'],
                'amenities': ['WiFi', 'First Aid', 'Refreshments'],
                'opening_time': time(5, 0),
                'closing_time': time(23, 0),
                'cancellation_policy': '2 hours advance notice required for cancellation.',
                'advance_booking_days': 14,
            },
            {
                'name': 'Fitness Hub',
                'description': 'Modern fitness center with indoor courts and swimming pool.',
                'address': '789 Wellness Street, Whitefield, Bengaluru, Karnataka 560066',
                'latitude': 12.9698,
                'longitude': 77.7500,
                'sports_available': ['swimming', 'squash', 'basketball'],
                'contact_number': '+919876543212',
                'email': 'hello@fitnesshub.com',
                'rating': 4.4,
                'images': ['/api/placeholder/400/300'],
                'price_per_hour': Decimal('350.00'),
                'facilities': ['Parking', 'Changing Room', 'Lockers', 'Towel Service'],
                'amenities': ['Steam Room', 'Sauna', 'WiFi', 'Juice Bar'],
                'opening_time': time(6, 0),
                'closing_time': time(21, 0),
                'cancellation_policy': '4 hours advance notice required for cancellation.',
                'advance_booking_days': 5,
            }
        ]
        
        created_clubs = []
        for club_data in clubs_data:
            club, created = SportsClub.objects.get_or_create(
                name=club_data['name'],
                defaults=club_data
            )
            if created:
                self.stdout.write(f"Created club: {club.name}")
                created_clubs.append(club)
            else:
                self.stdout.write(f"Club already exists: {club.name}")
                created_clubs.append(club)
        
        # Create time slots for next 30 days
        start_date = date.today()
        
        for club in created_clubs:
            slots_created = 0
            
            for day_offset in range(30):  # Next 30 days
                slot_date = start_date + timedelta(days=day_offset)
                
                # Skip if slots already exist for this date
                if TimeSlot.objects.filter(club=club, date=slot_date).exists():
                    continue
                
                # Create slots based on club's operating hours
                current_time = club.opening_time
                
                while current_time < club.closing_time:
                    # Calculate end time (1 hour slots)
                    end_hour = current_time.hour + 1
                    end_minute = current_time.minute
                    
                    if end_hour >= 24:
                        break
                    
                    end_time = time(end_hour, end_minute)
                    
                    # Create slots for each sport available at the club
                    for sport in club.sports_available:
                        TimeSlot.objects.create(
                            club=club,
                            date=slot_date,
                            start_time=current_time,
                            end_time=end_time,
                            sport=sport,
                            max_capacity=4 if sport in ['tennis', 'badminton'] else 20,
                            is_available=True
                        )
                        slots_created += 1
                    
                    # Move to next hour
                    current_time = end_time
            
            self.stdout.write(f"Created {slots_created} time slots for {club.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created sample data for {len(created_clubs)} clubs')
        )
