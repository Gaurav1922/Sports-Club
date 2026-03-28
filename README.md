# 🏆 Sports Club Booking System

A production-ready full-stack web application for sports facility slot booking with real-time availability, integrated payments, and comprehensive admin management.

**Live Demo:** [sports-booking-frontend-iz1f.onrender.com](https://sports-booking-frontend-iz1f.onrender.com)

---

## ✨ Features

### For Users
- 📱 **OTP-based authentication** — mobile number login, no password needed
- 🏟️ **Browse clubs** — search by name or location, view sports and pricing
- ⏰ **Real-time slot booking** — 1-hour slots from 6 AM to 10 PM
- 💳 **Multiple payment modes** — Card, UPI, NetBanking, Wallet
- 📋 **My Bookings** — status cards with cancel/refund options
- ⭐ **Reviews** — rate and review clubs after booking
- 📅 **15-day advance booking** limit enforced

### For Admins
- 📊 **Live dashboard** — stats, 7-day chart, recent activities (auto-refresh every 30s)
- 📋 **All Bookings** — filter by status, payment mode badges
- 🏢 **Manage Clubs** — add/edit/delete clubs and sports
- 📄 **Monthly PDF Report** — club-wise revenue breakdown, daily details
- 🔓 **Release expired slots** — manual cleanup button
- 🔑 **Passcode login** — skip OTP with admin passcode

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Tailwind CSS, Lucide Icons |
| Backend | Django 5.2, Django REST Framework |
| Database | PostgreSQL |
| Auth | JWT (SimpleJWT) + Mobile OTP |
| Payments | Stripe |
| SMS | Twilio |
| Hosting | Render (Backend + Frontend + DB) |
| Monitoring | UptimeRobot |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- PostgreSQL

### Backend Setup

```bash
cd backend/sports_booking
python -m venv sports_env
source sports_env/bin/activate  # Windows: sports_env\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend/sports-booking-app
npm install
```

Create `.env.local`:
```env
REACT_APP_API_URL=http://localhost:8000/api
```

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000)

---

## 📁 Project Structure

```
sports-booking-system/
├── backend/
│   └── sports_booking/
│       ├── accounts/          # Auth, OTP, user management
│       ├── bookings/          # Slot booking, locking, waitlist
│       ├── clubs/             # Club, sport, review management
│       ├── payments/          # Stripe integration, payment flow
│       ├── sports_booking/    # Django settings, URLs
│       ├── requirements.txt
│       └── build.sh           # Render build script
└── frontend/
    └── sports-booking-app/
        ├── src/
        │   └── App.js         # Single-page React application
        ├── public/
        └── package.json
```

---

## 🌐 API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/send-otp/` | Send OTP to mobile |
| POST | `/api/auth/verify-otp/` | Verify OTP, get JWT |
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/admin-login/` | Admin passcode login |
| GET | `/api/auth/health/` | Health check |

### Bookings
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/bookings/available_slots/` | Get available slots |
| POST | `/api/bookings/lock_slot/` | Lock slot for 10 min |
| GET/POST | `/api/bookings/` | List/create bookings |

### Clubs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/clubs/` | List all clubs |
| GET/POST | `/api/clubs/reviews/` | Get/add reviews |
| GET/POST | `/api/clubs/<id>/sports/` | Manage sports |

### Payments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/payments/confirm/` | Confirm payment |

---

## ☁️ Deployment (Render)

### Backend (Web Service)
- **Root Directory:** `backend/sports_booking`
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- **Start Command:** `gunicorn sports_booking.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### Frontend (Static Site)
- **Root Directory:** `frontend/sports-booking-app`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `build`

### Required Environment Variables

```env
SECRET_KEY=
DEBUG=False
DATABASE_URL=
STRIPE_SECRET_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CORS_ALLOWED_ORIGINS=
PAYMENT_DEV_MODE=False
```

---

## 🔒 Security Features

- JWT authentication with 7-day token expiry
- OTP with 10-minute expiry, single-use
- CORS restricted to frontend domain
- HTTPS enforced in production
- SQL injection prevention via Django ORM
- XSS and clickjacking protection headers
- Secrets managed via environment variables

---

## 📊 Booking Flow

```
User selects Club → Chooses Sport → Picks Date
    → Views available slots (real-time)
    → Locks slot (10-min hold)
    → Completes payment (Card/UPI/NetBanking/Wallet)
    → Booking confirmed ✓
    → Slot locked for other users
```

---

## 🛡️ Business Rules

- Slots available from **6 AM to 10 PM** in 1-hour intervals
- Slot locks expire after **10 minutes** if payment not completed
- Bookings can only be made up to **15 days** in advance
- Cancellations allowed only **24 hours** before booking time
- Confirmed + paid bookings get refunded on cancellation

---
"""
## 📸 Screenshots

| Feature | Description |
|---|---|
| Login | OTP-based mobile authentication |
| Clubs | Card grid with sports badges and ratings |
| Booking | Date picker, slot grid, payment form |
| My Bookings | Status-coded cards with action buttons |
| Admin Dashboard | Live stats, chart, recent activities |
| Monthly Report | Club-wise breakdown, daily table, printable |

---
"""
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational and portfolio purposes.

---

## 👤 Author

**Gaurav M**
- GitHub: [@Gaurav1922](https://github.com/Gaurav1922)
- Project: [github.com/Gaurav1922/Sports-Club](https://github.com/Gaurav1922/Sports-Club)

---

