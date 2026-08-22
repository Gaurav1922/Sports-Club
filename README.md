# Sports Club — Booking System

A full-stack sports facility booking platform where users can browse clubs, book time slots for sports like cricket, badminton, football, and more, and pay online. Includes an admin dashboard for managing clubs, bookings, and revenue.

**Live demo:** https://sports-club-frontend-dbpn.onrender.com

## Features

### For users
- Mobile OTP-based registration and login (via Twilio)
- Browse clubs and available sports with pricing
- Real-time slot availability with temporary slot locking (prevents double-booking)
- Secure payments via Stripe — supports Card, UPI, and NetBanking
- Booking history with status tracking (pending, confirmed, cancelled, refunded)
- Resume payment on an incomplete/pending booking
- Waitlist notifications when a slot is full
- Email and SMS booking confirmations

### For admins
- Dashboard with revenue, booking, and user stats
- Manage clubs and sports (add, edit, delete)
- View and update all bookings across the platform
- Monthly revenue reports by club and sport
- Admin-only login with passcode-based authentication

## Tech stack

**Backend**
- Django 5 + Django REST Framework
- PostgreSQL (hosted on [Neon](https://neon.tech))
- Redis for caching and slot locks (Memurai locally on Windows)
- Celery for background tasks (confirmation emails/SMS)
- JWT authentication (`djangorestframework-simplejwt`)
- Stripe for payments
- Twilio for OTP and SMS notifications
- Resend for transactional email delivery

**Frontend**
- React (Create React App)
- Tailwind CSS
- Stripe.js / React Stripe.js (`PaymentElement`)
- Lucide icons

**Deployment**
- Backend: Render (Web Service)
- Frontend: Render (Static Site)
- Database: Neon (pooled Postgres connection)
- Cache/locks: Redis (Render-hosted)

## Project structure

```
sports-booking-system/
├── backend/
│   ├── .env                    # local secrets (not tracked)
│   ├── .env.example            # template for required env vars
│   └── sports_booking/
│       ├── accounts/           # auth, OTP, admin views
│       ├── bookings/           # booking logic, slot locks, waitlist, tasks
│       ├── clubs/              # club and sport models
│       ├── payments/           # Stripe integration
│       ├── sports_booking/     # settings, urls, celery config
│       ├── manage.py
│       ├── requirements.txt
│       └── build.sh            # Render build/deploy script
└── frontend/
    └── sports-booking-app/
        ├── src/
        │   └── App.js
        ├── package.json
        └── .npmrc
```

## Getting started locally

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL (or use SQLite for quick local testing)
- Redis / Memurai (Windows)
- Stripe, Twilio, and Resend accounts (free tiers work for development)

### Backend setup

```bash
cd backend
python -m venv sports_env
sports_env\Scripts\activate      # Windows
# source sports_env/bin/activate # macOS/Linux

pip install -r sports_booking/requirements.txt
cp .env.example .env             # then fill in your own values
```

Required environment variables (see `.env.example`):

```
SECRET_KEY=
DEBUG=True
DATABASE_URL=
REDIS_URL=
ADMIN_PASSCODE=
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Run migrations and start the server:

```bash
cd sports_booking
python manage.py migrate
python manage.py runserver
```

### Frontend setup

```bash
cd frontend/sports-booking-app
npm install
```

Create `.env` in this folder:

```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

```bash
npm start
```

The app runs at `http://localhost:3000`, connecting to the Django API at `http://localhost:8000`.

## Deployment notes

- The backend's `build.sh` runs migrations, collects static files, and creates the initial superuser from `DJANGO_SUPERUSER_PASSWORD` (never hardcoded).
- Use Neon's **pooled** connection string (hostname containing `-pooler`) for `DATABASE_URL` in production.
- Email delivery uses Resend's HTTP API rather than SMTP, since most cloud hosts (including Render) block outbound SMTP ports.
- `CELERY_TASK_ALWAYS_EAGER=True` runs background tasks (email/SMS) synchronously within the request — suitable for low-traffic deployments without a dedicated worker process. For production traffic, run a separate Celery worker instead.

## Security

- Secrets are managed exclusively through environment variables — never committed to the repo.
- Rate limiting is applied to authentication endpoints (OTP, login, admin login).
- Payment confirmation validates the Stripe PaymentIntent's amount and metadata against the booking before marking it as paid, preventing intent-replay across bookings.
- See `.gitignore` for excluded files (`.env`, `db.sqlite3`, compiled Python artifacts, local logs).

## License

This project is for portfolio/demonstration purposes.
