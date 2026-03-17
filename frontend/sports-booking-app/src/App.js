import React, { useState, useEffect } from 'react';
import { AlertCircle, Calendar, Clock, MapPin, User, LogOut, CreditCard, Search, Menu, X, Star, Users, TrendingUp, DollarSign, Plus, Edit, Trash2, Lock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = {
  sendOTP: (mobile) => fetch(`${API_BASE_URL}/auth/send-otp/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mobile_number: mobile })
  }),

  verifyOTP: (mobile, otp) => fetch(`${API_BASE_URL}/auth/verify-otp/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mobile_number: mobile, otp })
  }),

  register: (userData) => fetch(`${API_BASE_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  }),

  getClubs: (token) => fetch(`${API_BASE_URL}/clubs/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  getClubDetails: (token, clubId) => fetch(`${API_BASE_URL}/clubs/${clubId}/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  getAvailableSlots: (token, clubId, sportId, date) => fetch(
    `${API_BASE_URL}/bookings/available_slots/?club=${clubId}&sport=${sportId}&date=${date}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  ),

  lockSlot: (token, slotData) => fetch(`${API_BASE_URL}/bookings/lock_slot/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(slotData)
  }),

  getBookings: (token) => fetch(`${API_BASE_URL}/bookings/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  createBooking: (token, bookingData) => fetch(`${API_BASE_URL}/bookings/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(bookingData)
  }),

  createPaymentIntent: (token, bookingId) => fetch(`${API_BASE_URL}/payments/create-intent/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ booking_id: bookingId })
  }),

  confirmPayment: (token, paymentData) => fetch(`${API_BASE_URL}/payments/confirm/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(paymentData)
  }),

  addReview: (token, reviewData) => fetch(`${API_BASE_URL}/clubs/reviews/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(reviewData)
  }),

  getReviews: (token, clubId) => fetch(`${API_BASE_URL}/clubs/${clubId}/reviews/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  getUserProfile: (token) => fetch(`${API_BASE_URL}/auth/profile/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  // Admin APIs
  getDashboardStats: (token) => fetch(`${API_BASE_URL}/auth/admin/dashboard-stats/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  getMonthlyReport: (token, month, year) => fetch(
    `${API_BASE_URL}/auth/admin/monthly-report/?month=${month}&year=${year}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  ),

  getAllBookings: (token) => fetch(`${API_BASE_URL}/auth/admin/bookings/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  updateBookingStatus: (token, bookingId, status) => fetch(
    `${API_BASE_URL}/auth/admin/bookings/${bookingId}/status/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status })
    }
  ),

  createClub: (token, clubData) => fetch(`${API_BASE_URL}/auth/admin/clubs/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(clubData)
  }),

  updateClub: (token, clubId, clubData) => fetch(`${API_BASE_URL}/auth/admin/clubs/${clubId}/`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(clubData)
  }),

  deleteClub: (token, clubId) => fetch(`${API_BASE_URL}/auth/admin/clubs/${clubId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  getClubSports: (token, clubId) => fetch(`${API_BASE_URL}/clubs/${clubId}/sports/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  addSport: (token, clubId, sportData) => fetch(`${API_BASE_URL}/clubs/${clubId}/sports/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(sportData)
  }),

  updateSport: (token, clubId, sportId, sportData) => fetch(`${API_BASE_URL}/clubs/${clubId}/sports/${sportId}/`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(sportData)
  }),

  deleteSport: (token, clubId, sportId) => fetch(`${API_BASE_URL}/clubs/${clubId}/sports/${sportId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  releaseExpiredSlots: (token) => fetch(`${API_BASE_URL}/bookings/release_expired_slots/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
  }),

  getWaitlist: (token) => fetch(`${API_BASE_URL}/bookings/waitlist/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),

  removeFromWaitlist: (token, waitlistId) => fetch(
    `${API_BASE_URL}/bookings/waitlist/${waitlistId}/`,
    {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    }
  )
};

// Multi-mode Payment Form
const StripePaymentForm = ({ amount, onSuccess, onCancel }) => {
  const [paymentMode, setPaymentMode] = useState('card');
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvc, setCvc] = useState('');
  const [cardName, setCardName] = useState('');
  const [upiId, setUpiId] = useState('');
  const [netbankingBank, setNetbankingBank] = useState('');
  const [processing, setProcessing] = useState(false);
  const [formError, setFormError] = useState('');

  const formatCardNumber = (val) => val.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim();
  const formatExpiry = (val) => {
    const d = val.replace(/\D/g, '').slice(0, 4);
    if (d.length === 0) return '';
    let month = d.slice(0, 2);
    if (month.length === 2 && parseInt(month) > 12) month = '12';
    if (month.length === 2 && parseInt(month) < 1) month = '01';
    return d.length >= 3 ? month + '/' + d.slice(2) : month;
  };

  const handleSubmit = () => {
    setFormError('');
    if (paymentMode === 'card') {
      if (cardNumber.replace(/\s/g, '').length !== 16) { setFormError('Enter a valid 16-digit card number.'); return; }
      if (!/^\d{2}\/\d{2}$/.test(expiry)) { setFormError('Enter expiry in MM/YY format.'); return; }
      const [mm, yy] = expiry.split('/');
      const month = parseInt(mm), year = parseInt('20' + yy);
      const now = new Date();
      if (month < 1 || month > 12) { setFormError('Month must be between 01 and 12.'); return; }
      if (year < now.getFullYear() || (year === now.getFullYear() && month < now.getMonth() + 1)) {
        setFormError('Card has expired. Please use a valid card.'); return;
      }
      if (cvc.length < 3) { setFormError('Enter a valid 3-digit CVC.'); return; }
      if (!cardName.trim()) { setFormError('Enter cardholder name.'); return; }
    } else if (paymentMode === 'upi') {
      if (!upiId.includes('@')) { setFormError('Enter a valid UPI ID (e.g. name@upi).'); return; }
    } else if (paymentMode === 'netbanking') {
      if (!netbankingBank) { setFormError('Please select your bank.'); return; }
    }
    setProcessing(true);
    setTimeout(() => {
      onSuccess({ paymentIntentId: 'pi_' + Math.random().toString(36).substr(2, 9), mode: paymentMode });
      setProcessing(false);
    }, 1500);
  };

  const modes = [
    { id: 'card', label: '💳 Card', desc: 'Credit / Debit Card' },
    { id: 'upi', label: '📱 UPI', desc: 'GPay, PhonePe, Paytm' },
    { id: 'netbanking', label: '🏦 Net Banking', desc: 'All major banks' },
    { id: 'wallet', label: '👛 Wallet', desc: 'Paytm, Amazon Pay' },
  ];

  const banks = ['State Bank of India', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 'Kotak Mahindra', 'Punjab National Bank', 'Bank of Baroda', 'Canara Bank'];

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-h-screen overflow-y-auto">
      <h3 className="text-xl font-bold mb-1">Complete Payment</h3>
      <p className="text-3xl font-bold text-indigo-600 mb-4">₹{amount}</p>

      {/* Payment Mode Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
        {modes.map(m => (
          <button
            key={m.id}
            onClick={() => { setPaymentMode(m.id); setFormError(''); }}
            className={`p-2 rounded-lg border text-center transition ${paymentMode === m.id ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'}`}
          >
            <div className="text-lg">{m.label.split(' ')[0]}</div>
            <div className="text-xs font-medium text-gray-700 mt-0.5">{m.label.split(' ').slice(1).join(' ')}</div>
            <div className="text-xs text-gray-400 hidden sm:block">{m.desc}</div>
          </button>
        ))}
      </div>

      {formError && <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{formError}</div>}

      {/* Card Form */}
      {paymentMode === 'card' && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Card Number</label>
            <input type="text" value={cardNumber} onChange={e => setCardNumber(formatCardNumber(e.target.value))}
              placeholder="4242 4242 4242 4242" className="w-full px-3 py-2 border rounded-lg text-sm" maxLength="19" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Cardholder Name</label>
            <input type="text" value={cardName} onChange={e => setCardName(e.target.value)}
              placeholder="Name on card" className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Expiry</label>
              <input type="text" value={expiry} onChange={e => setExpiry(formatExpiry(e.target.value))}
                placeholder="MM/YY" className="w-full px-3 py-2 border rounded-lg text-sm" maxLength="5" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">CVC</label>
              <input type="text" value={cvc} onChange={e => setCvc(e.target.value.replace(/\D/g, '').slice(0, 3))}
                placeholder="123" className="w-full px-3 py-2 border rounded-lg text-sm" maxLength="3" />
            </div>
          </div>
        </div>
      )}

      {/* UPI Form */}
      {paymentMode === 'upi' && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">UPI ID</label>
            <input type="text" value={upiId} onChange={e => setUpiId(e.target.value)}
              placeholder="yourname@upi" className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            {['GPay', 'PhonePe', 'Paytm', 'BHIM', 'Amazon Pay', 'Cred'].map(app => (
              <button key={app} onClick={() => setUpiId('')}
                className="p-2 border rounded-lg text-xs text-gray-600 hover:border-indigo-400 hover:bg-indigo-50">
                {app}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500">Enter your UPI ID or select your app above</p>
        </div>
      )}

      {/* Net Banking Form */}
      {paymentMode === 'netbanking' && (
        <div>
          <label className="block text-sm font-medium mb-2">Select Bank</label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {banks.map(bank => (
              <label key={bank} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer ${netbankingBank === bank ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'}`}>
                <input type="radio" name="bank" value={bank} checked={netbankingBank === bank}
                  onChange={() => setNetbankingBank(bank)} className="text-indigo-600" />
                <span className="text-sm text-gray-700">{bank}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Wallet Form */}
      {paymentMode === 'wallet' && (
        <div>
          <label className="block text-sm font-medium mb-2">Select Wallet</label>
          <div className="grid grid-cols-2 gap-2">
            {['Paytm Wallet', 'Amazon Pay', 'Mobikwik', 'Freecharge', 'Airtel Money', 'Jio Money'].map(w => (
              <button key={w} onClick={() => { setFormError(''); handleSubmit(); }}
                className="p-3 border rounded-lg text-sm text-gray-700 hover:border-indigo-500 hover:bg-indigo-50 text-left">
                {w}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3 mt-5">
        <button onClick={handleSubmit} disabled={processing}
          className="flex-1 bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 font-semibold">
          {processing ? 'Processing...' : `Pay ₹${amount}`}
        </button>
        <button onClick={onCancel} className="px-5 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
          Cancel
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-3 text-center">🔒 256-bit SSL encrypted · Your payment info is secure</p>
    </div>
  );
};

// Star Rating Component
const StarRating = ({ rating, onRatingChange, readonly = false }) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={`w-6 h-6 ${star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            } ${!readonly && 'cursor-pointer hover:text-yellow-400'}`}
          onClick={() => !readonly && onRatingChange && onRatingChange(star)}
        />
      ))}
    </div>
  );
};

function App() {
  const [currentView, setCurrentView] = useState('login');
  const [mobileMenu, setMobileMenu] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const [mobile, setMobile] = useState('');
  const [otp, setOTP] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [devOtp, setDevOtp] = useState(null); // shows OTP on screen in dev mode

  const [regData, setRegData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    mobile_number: ''
  });

  const [clubs, setClubs] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [bookingFilter, setBookingFilter] = useState('all');
  const [selectedClub, setSelectedClub] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [lockedSlot, setLockedSlot] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [pendingBooking, setPendingBooking] = useState(null);
  const [bookingConfirmation, setBookingConfirmation] = useState(null); // holds confirmed booking details
  const [waitlistedSlots, setWaitlistedSlots] = useState([]);
  const [showWaitlistNotification, setShowWaitlistNotification] = useState(false);
  const [waitlistMessage, setWaitlistMessage] = useState('');

  // Cancellation modal state
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelBooking, setCancelBooking] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelReasonOther, setCancelReasonOther] = useState('');

  // Review state
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [clubReviews, setClubReviews] = useState([]);

  // Admin state
  const [dashboardStats, setDashboardStats] = useState(null);
  const [allBookings, setAllBookings] = useState([]);
  const [showMonthlyReport, setShowMonthlyReport] = useState(false);
  const [monthlyReport, setMonthlyReport] = useState(null);
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());
  const [reportLoading, setReportLoading] = useState(false);
  const [adminBookingFilter, setAdminBookingFilter] = useState('all');
  const [showClubForm, setShowClubForm] = useState(false);
  const [editingClub, setEditingClub] = useState(null);
  const [clubFormData, setClubFormData] = useState({
    name: '',
    location: '',
    opening_time: '',
    closing_time: '',
    description: '',
    phone_number: ''
  });

  // Sports management state
  const [clubSports, setClubSports] = useState([]);
  const [managingSportsFor, setManagingSportsFor] = useState(null);
  const [showSportForm, setShowSportForm] = useState(false);
  const [editingSport, setEditingSport] = useState(null);
  const [sportFormData, setSportFormData] = useState({ name: '', price_per_hour: '', description: '', is_active: true });
  const SPORT_OPTIONS = ['Cricket', 'Badminton', 'Tennis', 'Football', 'Basketball', 'Volleyball', 'Table Tennis', 'Swimming', 'Squash', 'Hockey'];

  const [bookingForm, setBookingForm] = useState({
    club: null,
    sport: null,
    date: new Date().toISOString().split('T')[0],
    slot: null
  });

  // Auto-clear messages after 5 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError('');
        setSuccess('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // On mount — restore session + ping server to keep it warm
  useEffect(() => {
    // Keep-alive: ping health endpoint so server wakes up instantly for users
    fetch(`${API_BASE_URL.replace('/api', '')}/api/auth/health/`).catch(() => {});

    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      loadUserDataWithToken(savedToken);
    }
  }, []);

  const loadUserDataWithToken = async (activeToken) => {
    setLoading(true);
    try {
      const response = await api.getUserProfile(activeToken);
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        if (data.is_staff) {
          setCurrentView('admin-dashboard');
        } else {
          setCurrentView('clubs');
        }
      } else {
        logout();
      }
    } catch (err) {
      console.error('Failed to load user data:', err);
      setError('Failed to connect to server.');
    } finally {
      setLoading(false);
    }
  };

  const loadUserData = async () => {
    const savedToken = localStorage.getItem('token');
    if (!savedToken) return;
    await loadUserDataWithToken(savedToken);
  };

  const handleSendOTP = async () => {
    setError('');
    setSuccess('');

    if (!mobile || mobile.length !== 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    try {
      const response = await api.sendOTP(mobile);
      const data = await response.json();

      if (response.ok) {
        setOtpSent(true);
        // Dev mode: show OTP on screen if backend returns it
        if (data.otp) {
          setDevOtp(data.otp);
        }
        setSuccess(data.otp
          ? 'OTP generated (dev mode — see below)'
          : 'OTP sent successfully! Check your SMS.'
        );
      } else {
        setError(data.error || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Network error. Please check your backend is running.');
    }
  };

  const handleVerifyOTP = async () => {
    setError('');
    setSuccess('');

    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await api.verifyOTP(mobile, otp);
      const data = await response.json();

      if (response.ok) {
        if (data.user_exists && data.access) {
          // Existing user — log them in directly
          const accessToken = data.access;
          localStorage.setItem('token', accessToken);
          setToken(accessToken);
          setSuccess('Welcome back!');
          await loadUserDataWithToken(accessToken);
        } else {
          // New user — go to registration
          setIsVerified(true);
          setSuccess('OTP verified! Please complete registration.');
          setRegData(prev => ({ ...prev, mobile_number: mobile }));
          setCurrentView('register');
        }
      } else {
        setError(data.error || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    setError('');
    setSuccess('');

    if (!regData.username || !regData.email || !regData.first_name || !regData.last_name) {
      setError('Please fill all fields');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(regData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      const response = await api.register(regData);
      const data = await response.json();

      if (response.ok) {
        const accessToken = data.access;
        localStorage.setItem('token', accessToken);
        setToken(accessToken);
        setSuccess('Registration successful!');
        await loadUserDataWithToken(accessToken);
      } else {
        const errorMsg = typeof data === 'object'
          ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
          : (data.error || 'Registration failed');
        setError(errorMsg);
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    setCurrentView('login');
    setOtpSent(false);
    setIsVerified(false);
    setMobile('');
    setOTP('');
    setDevOtp(null);
  };

  const loadClubs = async () => {
    try {
      const response = await api.getClubs(token);
      if (response.ok) {
        const data = await response.json();
        const clubList = Array.isArray(data) ? data : (data.results || []);
        setClubs(clubList);
      } else {
        const err = await response.json().catch(() => ({}));
        setError(`Failed to load clubs: ${response.status} ${err.detail || err.error || ''}`);
      }
    } catch (err) {
      setError(`Failed to load clubs: ${err.message}`);
    }
  };

  const loadBookings = async () => {
    try {
      const response = await api.getBookings(token);
      if (response.ok) {
        const data = await response.json();
        setBookings(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) {
      setError('Failed to load bookings');
    }
  };

  const handleCancelBooking = (booking) => {
    // Policy: only future bookings can be cancelled, and only if > 24 hours away
    const bookingDateTime = new Date(`${booking.date}T${booking.start_time}`);
    const now = new Date();
    const hoursUntilBooking = (bookingDateTime - now) / (1000 * 60 * 60);

    if (hoursUntilBooking < 0) {
      setError('Cannot cancel a booking that has already passed.');
      return;
    }
    if (hoursUntilBooking < 24 && booking.status === 'confirmed') {
      setError('Cancellation is not allowed within 24 hours of the booking time.');
      return;
    }

    setCancelBooking(booking);
    setCancelReason('');
    setCancelReasonOther('');
    setShowCancelModal(true);
  };

  const handleConfirmCancellation = async () => {
    if (!cancelReason) { setError('Please select a reason for cancellation.'); return; }
    if (cancelReason === 'other' && !cancelReasonOther.trim()) {
      setError('Please describe your reason for cancellation.'); return;
    }

    const finalReason = cancelReason === 'other' ? cancelReasonOther : cancelReason;
    setLoading(true);
    setShowCancelModal(false);

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/bookings/${cancelBooking.id}/cancel/`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason: finalReason })
        }
      );
      const data = await response.json();
      if (response.ok) {
        setSuccess(
          data.status === 'refunded'
            ? `Booking cancelled. Refund of ₹${cancelBooking.amount} will be credited within 5-7 business days.`
            : 'Booking cancelled. Slot is now available for others.'
        );
        setCancelBooking(null);
        loadBookings();
      } else {
        setError(data.error || 'Failed to cancel booking');
      }
    } catch (err) {
      setError('Failed to cancel booking');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSlots = async (clubId, sportId, date) => {
    if (!clubId || !sportId || !date) return;
    try {
      const response = await api.getAvailableSlots(token, clubId, sportId, date);
      if (response.ok) {
        const data = await response.json();
        setAvailableSlots(Array.isArray(data) ? data : (data.results || data.slots || []));
      } else {
        const err = await response.json();
        setError(err.error || 'Failed to load slots');
      }
    } catch (err) {
      setError('Failed to load available slots');
    }
  };

  const handleSlotSelection = async (slot) => {
    if (slot.is_past) {
      setError('This slot has already passed. Please select a future time slot.');
      return;
    }
    if (slot.is_locked || slot.is_booked) {
      setError('This slot is not available');
      return;
    }

    setSelectedSlot(slot);

    // Lock the slot for 10 minutes
    try {
      const response = await api.lockSlot(token, {
        club: bookingForm.club,
        sport: bookingForm.sport,
        date: bookingForm.date,
        start_time: slot.start_time,
        end_time: slot.end_time
      });

      const data = await response.json();

      if (response.ok) {
        setLockedSlot(data);
        setSuccess('Slot reserved for 10 minutes. Please complete payment.');

        // Start countdown timer
        setTimeout(() => {
          if (!showPayment) {
            setLockedSlot(null);
            setSelectedSlot(null);
            setError('Slot reservation expired. Please select again.');
            loadAvailableSlots(bookingForm.club, bookingForm.sport, bookingForm.date);
          }
        }, 600000); // 10 minutes

      } else if (response.status === 409) {
        // User added to waitlist
        if (data.waitlisted) {
          setWaitlistMessage(data.error);
          setShowWaitlistNotification(true);
          setSuccess('');

          // Auto-hide after 8 seconds
          setTimeout(() => {
            setShowWaitlistNotification(false);
          }, 8000);
        } else {
          setError(data.error || 'Slot is no longer available');
        }
        loadAvailableSlots(bookingForm.club, bookingForm.sport, bookingForm.date);
      } else {
        setError(data.error || 'Failed to lock slot');
        loadAvailableSlots(bookingForm.club, bookingForm.sport, bookingForm.date);
      }
    } catch (err) {
      setError('Failed to lock slot');
    }
  };

  const loadWaitlist = async () => {
    try {
      const response = await api.getWaitlist(token);
      if (response.ok) {
        const data = await response.json();
        setWaitlistedSlots(data);
      }
    } catch (err) {
      console.error('Failed to load waitlist');
    }
  };

  const handleRemoveFromWaitlist = async (waitlistId) => {
    try {
      const response = await api.removeFromWaitlist(token, waitlistId);
      if (response.ok) {
        setSuccess('Removed from waitlist');
        loadWaitlist();
      }
    } catch (err) {
      setError('Failed to remove from waitlist');
    }
  };

  const handleCreateBooking = async () => {
    if (!selectedSlot) return;

    try {
      const response = await api.createBooking(token, {
        club: bookingForm.club,
        sport: bookingForm.sport,
        date: bookingForm.date,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
        lock_id: lockedSlot?.id
      });

      if (response.ok) {
        const data = await response.json();
        setPendingBooking(data);
        setShowPayment(true);
      } else {
        setError('Failed to create booking');
      }
    } catch (err) {
      setError('Failed to create booking');
    }
  };

  const handlePaymentSuccess = async (paymentData) => {
    try {
      const response = await api.confirmPayment(token, {
        booking_id: pendingBooking.id,
        payment_intent_id: paymentData?.paymentIntentId || `pi_dev_${Date.now()}`,
        payment_method: paymentData?.mode || 'card'
      });

      if (response.ok) {
        // Store full confirmation details for the welcome card
        setBookingConfirmation({
          user: user,
          booking: pendingBooking,
          club: selectedClub,
          slot: selectedSlot,
          paymentMode: paymentData?.mode || 'card',
          confirmedAt: new Date().toLocaleString('en-IN', {
            dateStyle: 'medium', timeStyle: 'short'
          })
        });
        setShowPayment(false);
        setPendingBooking(null);
        setSelectedSlot(null);
        setLockedSlot(null);
        setCurrentView('booking-confirmed');
        loadBookings();
      } else {
        setError('Payment confirmation failed');
      }
    } catch (err) {
      setError('Payment confirmation failed');
    }
  };

  const handleAddReview = async () => {
    if (!reviewRating || !reviewText) {
      setError('Please provide rating and review');
      return;
    }

    try {
      const response = await api.addReview(token, {
        club: selectedClub.id,
        rating: reviewRating,
        comment: reviewText
      });

      if (response.ok) {
        setSuccess('Review submitted successfully!');
        setShowReviewForm(false);
        setReviewRating(5);
        setReviewText('');
        loadClubReviews(selectedClub.id);
      } else {
        setError('Failed to submit review');
      }
    } catch (err) {
      setError('Failed to submit review');
    }
  };

  const loadClubReviews = async (clubId) => {
    try {
      const response = await api.getReviews(token, clubId);
      if (response.ok) {
        const data = await response.json();
        setClubReviews(data);
      }
    } catch (err) {
      console.error('Failed to load reviews');
    }
  };

  // Admin functions
  const loadDashboardStats = async () => {
    try {
      const response = await api.getDashboardStats(token);
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      }
    } catch (err) {
      console.error('Failed to load stats');
    }
  };

  const loadAllBookings = async () => {
    try {
      const response = await api.getAllBookings(token);
      if (response.ok) {
        const data = await response.json();
        setAllBookings(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) {
      setError('Failed to load bookings');
    }
  };

  const handleUpdateBookingStatus = async (bookingId, status) => {
    try {
      const response = await api.updateBookingStatus(token, bookingId, status);
      if (response.ok) {
        setSuccess('Booking status updated. Notification sent to user.');
        loadAllBookings();
      } else {
        setError('Failed to update status');
      }
    } catch (err) {
      setError('Failed to update status');
    }
  };

  const handleSaveClub = async () => {
    if (!clubFormData.name.trim()) { setError('Club name is required'); return; }
    if (!clubFormData.location.trim()) { setError('Location is required'); return; }
    if (!clubFormData.opening_time || !clubFormData.closing_time) { setError('Opening and closing times are required'); return; }
    if (clubFormData.phone_number && !/^\d{10}$/.test(clubFormData.phone_number)) {
      setError('Phone number must be exactly 10 digits'); return;
    }

    try {
      const response = editingClub
        ? await api.updateClub(token, editingClub.id, clubFormData)
        : await api.createClub(token, clubFormData);

      if (response.ok) {
        const savedClub = await response.json();
        setSuccess(editingClub ? 'Club updated!' : 'Club created! Now add sports to your club.');
        setShowClubForm(false);
        setEditingClub(null);
        setClubFormData({ name: '', location: '', opening_time: '', closing_time: '', description: '', phone_number: '' });
        loadClubs();

        // For new clubs — auto-open sports management modal
        if (!editingClub) {
          setManagingSportsFor(savedClub);
          setClubSports([]);
          setShowSportForm(true);
          setSportFormData({ name: '', price_per_hour: '', description: '', is_active: true });
        }
      } else {
        const data = await response.json().catch(() => ({}));
        setError(Object.values(data).flat().join(', ') || 'Failed to save club');
      }
    } catch (err) {
      setError('Failed to save club');
    }
  };

  const handleDeleteClub = async (clubId) => {
    if (!window.confirm('Are you sure you want to delete this club?')) return;

    try {
      const response = await api.deleteClub(token, clubId);
      if (response.ok) {
        setSuccess('Club deleted successfully');
        loadClubs();
      } else {
        setError('Failed to delete club');
      }
    } catch (err) {
      setError('Failed to delete club');
    }
  };

  const loadClubSports = async (clubId) => {
    try {
      const response = await api.getClubSports(token, clubId);
      if (response.ok) {
        const data = await response.json();
        setClubSports(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) {
      setError('Failed to load sports');
    }
  };

  const handleSaveSport = async () => {
    if (!sportFormData.name) { setError('Sport name is required'); return; }
    if (!sportFormData.price_per_hour || sportFormData.price_per_hour <= 0) { setError('Enter a valid price'); return; }

    try {
      const response = editingSport
        ? await api.updateSport(token, managingSportsFor.id, editingSport.id, sportFormData)
        : await api.addSport(token, managingSportsFor.id, sportFormData);

      if (response.ok) {
        setSuccess(editingSport ? 'Sport updated!' : 'Sport added!');
        setShowSportForm(false);
        setEditingSport(null);
        setSportFormData({ name: '', price_per_hour: '', description: '', is_active: true });
        loadClubSports(managingSportsFor.id);
        loadClubs();
      } else {
        const data = await response.json();
        setError(Object.values(data).flat().join(', ') || 'Failed to save sport');
      }
    } catch (err) {
      setError('Failed to save sport');
    }
  };

  const handleDeleteSport = async (sportId) => {
    if (!window.confirm('Delete this sport?')) return;
    try {
      const response = await api.deleteSport(token, managingSportsFor.id, sportId);
      if (response.ok) {
        setSuccess('Sport deleted');
        loadClubSports(managingSportsFor.id);
        loadClubs();
      } else {
        setError('Failed to delete sport');
      }
    } catch (err) {
      setError('Failed to delete sport');
    }
  };

  useEffect(() => {
    if (token) {
      if (currentView === 'clubs') loadClubs();
      if (currentView === 'bookings') loadBookings();
      if (currentView === 'waitlist') loadWaitlist();
      if (currentView === 'admin-dashboard' && user?.is_staff) {
        loadDashboardStats();
        loadClubs();
      }
      if (currentView === 'admin-bookings' && user?.is_staff) loadAllBookings();
      if (currentView === 'admin-clubs' && user?.is_staff) loadClubs();
    }
  }, [currentView, token]);

  const filteredClubs = clubs.filter(club =>
    club.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    club.location?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Calendar className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800">Sports Club</h1>
            <p className="text-gray-600 mt-2">Book your favorite sports facilities</p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-lg text-sm">
              {success}
            </div>
          )}

          {currentView === 'login' && !otpSent && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>
                <input
                  type="tel"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendOTP()}
                  placeholder="Enter 10-digit mobile number"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  maxLength="10"
                />
              </div>
              <button
                onClick={handleSendOTP}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
              >
                Send OTP
              </button>
            </div>
          )}

          {currentView === 'login' && otpSent && !isVerified && (
            <div className="space-y-4">
              {/* Dev Mode OTP Banner */}
              {devOtp && (
                <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 text-center">
                  <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">🔧 Dev Mode — Your OTP</p>
                  <div className="flex items-center justify-center gap-3">
                    <span className="text-4xl font-mono font-bold text-amber-700 tracking-widest">{devOtp}</span>
                    <button
                      onClick={() => { setOTP(devOtp); setDevOtp(null); }}
                      className="px-3 py-1.5 bg-amber-500 text-white text-xs rounded-lg hover:bg-amber-600 font-medium"
                    >
                      Auto-fill
                    </button>
                  </div>
                  <p className="text-xs text-amber-500 mt-1">Remove this before going to production</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Enter OTP</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOTP(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleVerifyOTP()}
                  placeholder="Enter 6-digit OTP"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  maxLength="6"
                />
              </div>
              <button
                onClick={handleVerifyOTP}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
              >
                Verify OTP
              </button>
              <button
                onClick={() => { setOtpSent(false); setOTP(''); setDevOtp(null); }}
                className="w-full text-indigo-600 py-2 text-sm hover:text-indigo-800"
              >
                Change Mobile Number
              </button>
            </div>
          )}

          {currentView === 'register' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
                <input
                  type="text"
                  value={regData.username}
                  onChange={(e) => setRegData({ ...regData, username: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  value={regData.email}
                  onChange={(e) => setRegData({ ...regData, email: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                  <input
                    type="text"
                    value={regData.first_name}
                    onChange={(e) => setRegData({ ...regData, first_name: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                  <input
                    type="text"
                    value={regData.last_name}
                    onChange={(e) => setRegData({ ...regData, last_name: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
              <button
                onClick={handleRegister}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition"
              >
                Complete Registration
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          #print-report, #print-report * { visibility: visible !important; }
          #print-report { position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; background: white; padding: 24px; }
          @page { margin: 1.5cm; size: A4 portrait; }
        }
      `}</style>
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <Calendar className="w-8 h-8 text-indigo-600" />
              <span className="text-xl font-bold text-gray-800">Sports Club</span>
            </div>

            <div className="hidden md:flex items-center gap-6">
              {user?.is_staff ? (
                <>
                  <button
                    onClick={() => setCurrentView('admin-dashboard')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'admin-dashboard' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    Dashboard
                  </button>
                  <button
                    onClick={() => setCurrentView('admin-bookings')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'admin-bookings' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    All Bookings
                  </button>
                  <button
                    onClick={() => setCurrentView('admin-clubs')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'admin-clubs' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    Manage Clubs
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setCurrentView('clubs')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'clubs' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    Clubs
                  </button>
                  <button
                    onClick={() => setCurrentView('bookings')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'bookings' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    My Bookings
                  </button>
                  <button
                    onClick={() => setCurrentView('waitlist')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'waitlist' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    My Waitlist
                    {!user?.is_staff && waitlistedSlots.length > 0 && (
                      <div className="relative">
                        <span className="ml-2 px-2 py-0.5 bg-yellow-400 text-yellow-900 text-xs rounded-full">
                          {waitlistedSlots.length}
                        </span>
                      </div>
                    )}
                  </button>
                  <button
                    onClick={() => setCurrentView('profile')}
                    className={`px-4 py-2 rounded-lg transition ${currentView === 'profile' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                      }`}
                  >
                    Profile
                  </button>
                </>
              )}
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>

            <button
              onClick={() => setMobileMenu(!mobileMenu)}
              className="md:hidden p-2"
            >
              {mobileMenu ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {mobileMenu && (
            <div className="md:hidden pb-4 space-y-2">
              {user?.is_staff ? (
                <>
                  <button
                    onClick={() => { setCurrentView('admin-dashboard'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    Dashboard
                  </button>
                  <button
                    onClick={() => { setCurrentView('admin-bookings'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    All Bookings
                  </button>
                  <button
                    onClick={() => { setCurrentView('admin-clubs'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    Manage Clubs
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => { setCurrentView('clubs'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    Clubs
                  </button>
                  <button
                    onClick={() => { setCurrentView('bookings'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    My Bookings
                  </button>
                  <button
                    onClick={() => {
                      setCurrentView('waitlist');
                      setMobileMenu(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    My Waitlist
                    {!user?.is_staff && waitlistedSlots.length > 0 && (
                      <div className="relative">
                        <span className="ml-2 px-2 py-0.5 bg-yellow-400 text-yellow-900 text-xs rounded-full">
                          {waitlistedSlots.length}
                        </span>
                      </div>
                    )}
                  </button>
                  <button
                    onClick={() => { setCurrentView('profile'); setMobileMenu(false); }}
                    className="block w-full text-left px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                  >
                    Profile
                  </button>
                </>
              )}
              <button
                onClick={logout}
                className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {success}
          </div>
        )}

        {/* Monthly Report Modal */}
        {showMonthlyReport && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl mt-6 mb-6">
              {/* Header — not printed */}
              <div className="flex justify-between items-center p-5 border-b no-print">
                <h3 className="text-xl font-bold text-gray-800">📊 Monthly Booking Report</h3>
                <button onClick={() => { setShowMonthlyReport(false); setMonthlyReport(null); }}
                  className="text-gray-400 hover:text-gray-600 text-2xl">✕</button>
              </div>

              {/* Selector — not printed */}
              <div className="p-5 border-b bg-gray-50 no-print">
                <div className="flex gap-3 items-end flex-wrap">
                  <div>
                    <label className="block text-xs font-medium mb-1 text-gray-600">Month</label>
                    <select value={reportMonth} onChange={e => setReportMonth(parseInt(e.target.value))}
                      className="px-3 py-2 border rounded-lg text-sm bg-white">
                      {['January','February','March','April','May','June','July','August','September','October','November','December']
                        .map((m, i) => <option key={i} value={i+1}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1 text-gray-600">Year</label>
                    <select value={reportYear} onChange={e => setReportYear(parseInt(e.target.value))}
                      className="px-3 py-2 border rounded-lg text-sm bg-white">
                      {[2024,2025,2026,2027].map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                  </div>
                  <button
                    onClick={async () => {
                      setReportLoading(true);
                      try {
                        const res = await api.getMonthlyReport(token, reportMonth, reportYear);
                        const data = await res.json();
                        setMonthlyReport(data);
                      } catch (e) { setError('Failed to load report'); }
                      finally { setReportLoading(false); }
                    }}
                    disabled={reportLoading}
                    className="px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium disabled:bg-gray-400"
                  >
                    {reportLoading ? 'Loading...' : 'Generate Report'}
                  </button>
                  {monthlyReport && (
                    <button onClick={() => window.print()}
                      className="px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium">
                      🖨 Print / Save PDF
                    </button>
                  )}
                </div>
              </div>

              {/* ── PRINTABLE REPORT CONTENT ── */}
              {monthlyReport && (
                <div id="print-report" className="p-6">
                  {/* Report Title — shows in print */}
                  <div className="mb-5 pb-4 border-b">
                    <h2 className="text-2xl font-bold text-gray-800">📊 Monthly Booking Report</h2>
                    <p className="text-gray-500 text-sm mt-0.5">{monthlyReport.month_name}</p>
                  </div>

                  {/* Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                    {[
                      { label: 'Total Bookings', value: monthlyReport.total_bookings, color: 'indigo' },
                      { label: 'Confirmed', value: monthlyReport.confirmed_bookings, color: 'green' },
                      { label: 'Net Revenue', value: `₹${monthlyReport.net_revenue.toLocaleString('en-IN')}`, color: 'purple' },
                      { label: 'Total Refunds', value: `₹${monthlyReport.total_refunds.toLocaleString('en-IN')}`, color: 'red' },
                    ].map((card, i) => (
                      <div key={i} className={`border border-${card.color}-200 rounded-lg p-3 text-center`}>
                        <p className={`text-xs font-semibold text-${card.color}-500 uppercase mb-1`}>{card.label}</p>
                        <p className={`text-xl font-bold text-${card.color}-700`}>{card.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Club-wise Breakdown */}
                  <h4 className="text-base font-bold text-gray-800 mb-3 border-b pb-1">Club-wise Breakdown</h4>
                  {monthlyReport.club_breakdown.length === 0 ? (
                    <p className="text-gray-400 text-sm text-center py-4">No booking data for this month</p>
                  ) : (
                    <div className="space-y-3 mb-6">
                      {monthlyReport.club_breakdown.map((club, i) => (
                        <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                          <div className="bg-gray-50 px-4 py-2 flex justify-between items-center">
                            <div>
                              <span className="font-bold text-gray-800 text-sm">{club.club_name}</span>
                              <span className="text-gray-400 text-xs ml-2">— {club.location}</span>
                            </div>
                            <span className="text-sm font-bold text-green-700">Net ₹{club.net_revenue.toLocaleString('en-IN')}</span>
                          </div>
                          <div className="px-4 py-2">
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs mb-2">
                              <div><p className="text-gray-400">Total</p><p className="font-bold text-gray-700">{club.total_bookings}</p></div>
                              <div><p className="text-green-500">Confirmed</p><p className="font-bold text-green-700">{club.confirmed}</p></div>
                              <div><p className="text-red-400">Cancelled</p><p className="font-bold text-red-600">{club.cancelled}</p></div>
                              <div><p className="text-blue-400">Refunded</p><p className="font-bold text-blue-600">{club.refunded}</p></div>
                            </div>
                            {club.sports.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {club.sports.map((s, j) => (
                                  <span key={j} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded text-xs">
                                    {s.name}: {s.bookings} · ₹{s.revenue.toLocaleString('en-IN')}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Daily Booking Details */}
                  <h4 className="text-base font-bold text-gray-800 mb-3 border-b pb-1">Daily Booking Details</h4>
                  <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500">Date</th>
                        <th className="px-3 py-2 text-center text-xs font-semibold text-gray-500">Total</th>
                        <th className="px-3 py-2 text-center text-xs font-semibold text-gray-500">Confirmed</th>
                        <th className="px-3 py-2 text-right text-xs font-semibold text-gray-500">Revenue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {monthlyReport.daily_data.filter(d => d.bookings > 0).length === 0 ? (
                        <tr><td colSpan="4" className="px-3 py-4 text-center text-gray-400 text-xs">No bookings this month</td></tr>
                      ) : (
                        monthlyReport.daily_data.filter(d => d.bookings > 0).map((day, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-3 py-1.5 text-xs font-medium text-gray-700">{day.day}</td>
                            <td className="px-3 py-1.5 text-center text-xs">{day.bookings}</td>
                            <td className="px-3 py-1.5 text-center text-xs text-green-600 font-medium">{day.confirmed}</td>
                            <td className="px-3 py-1.5 text-right text-xs font-semibold">₹{day.revenue.toLocaleString('en-IN')}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                    <tfoot className="bg-gray-50 font-bold text-xs">
                      <tr>
                        <td className="px-3 py-2">Total</td>
                        <td className="px-3 py-2 text-center">{monthlyReport.total_bookings}</td>
                        <td className="px-3 py-2 text-center text-green-700">{monthlyReport.confirmed_bookings}</td>
                        <td className="px-3 py-2 text-right text-green-700">₹{monthlyReport.gross_revenue.toLocaleString('en-IN')}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
        {/* Cancellation Modal */}
        {showCancelModal && cancelBooking && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-1">Cancel Booking</h3>
              <p className="text-sm text-gray-500 mb-4">
                {cancelBooking.club_name} — {cancelBooking.sport_name} on {cancelBooking.date} at {cancelBooking.start_time}
              </p>

              {cancelBooking.status === 'confirmed' && (
                <div className="bg-blue-50 border border-blue-300 rounded-lg p-4 mb-4">
                  <p className="text-sm font-semibold text-blue-800 mb-1">💳 Refund Policy</p>
                  <p className="text-sm text-blue-700">
                    A refund of <strong>₹{cancelBooking.amount}</strong> will be credited back to your <strong>original payment method</strong> within <strong>5–7 business days</strong>.
                  </p>
                  <p className="text-xs text-blue-500 mt-1">Refunds are processed automatically once cancellation is confirmed.</p>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Reason for cancellation <span className="text-red-500">*</span></label>
                <div className="space-y-2">
                  {[
                    'Change of plans',
                    'Found a better slot',
                    'Health or personal emergency',
                    'Weather conditions',
                    'Travelling / Out of town',
                    'other'
                  ].map(reason => (
                    <label key={reason} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="cancelReason"
                        value={reason}
                        checked={cancelReason === reason}
                        onChange={() => setCancelReason(reason)}
                        className="text-indigo-600"
                      />
                      <span className="text-sm text-gray-700 capitalize">{reason === 'other' ? 'Other (please specify)' : reason}</span>
                    </label>
                  ))}
                </div>
                {cancelReason === 'other' && (
                  <textarea
                    value={cancelReasonOther}
                    onChange={e => setCancelReasonOther(e.target.value)}
                    placeholder="Please describe your reason..."
                    className="mt-2 w-full px-3 py-2 border rounded-lg text-sm"
                    rows={3}
                  />
                )}
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 text-xs text-yellow-700">
                ⚠ <strong>Cancellation Policy:</strong> Cancellations are allowed up to 24 hours before the booking time. No refund for cancellations within 24 hours.
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => { setShowCancelModal(false); setCancelBooking(null); }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Keep Booking
                </button>
                <button
                  onClick={handleConfirmCancellation}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 font-medium"
                >
                  {loading ? 'Processing...' : 'Confirm Cancellation'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Payment Modal */}
        {showPayment && pendingBooking && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="max-w-md w-full">
              <StripePaymentForm
                amount={pendingBooking.amount}
                onSuccess={handlePaymentSuccess}
                onCancel={() => {
                  setShowPayment(false);
                  setError('Payment cancelled. Your slot will be released.');
                }}
              />
            </div>
          </div>
        )}
        {showWaitlistNotification && (
          <div className="fixed top-20 right-4 z-50 max-w-md animate-slide-in">
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg shadow-lg">
              <div className="flex items-start">
                <AlertTriangle className="w-6 h-6 text-yellow-400 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                    Slot Currently Unavailable
                  </h3>
                  <p className="text-sm text-yellow-700 mb-2">
                    {waitlistMessage}
                  </p>
                  <button
                    onClick={() => setShowWaitlistNotification(false)}
                    className="text-xs text-yellow-800 hover:text-yellow-900 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {/* Admin Dashboard */}
        {currentView === 'admin-dashboard' && user?.is_staff && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-800">Admin Dashboard</h2>
              <button
                onClick={async () => {
                  try {
                    const res = await api.releaseExpiredSlots(token);
                    const data = await res.json();
                    setSuccess(data.message || 'Expired slots released!');
                    loadDashboardStats();
                  } catch (e) {
                    setError('Failed to release expired slots');
                  }
                }}
                className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm font-medium"
              >
                🔓 Release Expired Slots
              </button>
              <button
                onClick={() => setShowMonthlyReport(true)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
              >
                📊 Monthly Report
              </button>
            </div>

            {dashboardStats && (
              <>
                {/* Compact Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: 'Total Bookings', value: dashboardStats.total_bookings, sub: `✓ ${dashboardStats.confirmed_bookings || 0} confirmed`, color: 'indigo' },
                    { label: 'Net Revenue', value: `₹${(dashboardStats.net_revenue ?? 0).toLocaleString('en-IN')}`, sub: `↩ ₹${dashboardStats.total_refunded || 0} refunded`, color: 'green' },
                    { label: 'Active Users', value: dashboardStats.active_users, sub: 'registered users', color: 'blue' },
                    { label: "Today's Bookings", value: dashboardStats.today_bookings, sub: `⏳ ${dashboardStats.pending_bookings || 0} pending`, color: 'purple' },
                  ].map((card, i) => (
                    <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-100 px-4 py-3">
                      <p className="text-xs text-gray-500 mb-1">{card.label}</p>
                      <p className={`text-2xl font-bold text-${card.color}-700`}>{card.value}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{card.sub}</p>
                    </div>
                  ))}
                </div>

                {/* Compact 7-Day Chart */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 px-4 py-3 mb-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Bookings — Last 7 Days</p>
                  {(() => {
                    const chartData = dashboardStats.weekly_bookings || [];
                    const maxVal = Math.max(...chartData.map(d => d.count), 1);
                    return (
                      <div className="flex items-end gap-2 h-20">
                        {chartData.map((day, i) => (
                          <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                            <span className="text-xs text-gray-600">{day.count > 0 ? day.count : ''}</span>
                            <div className="w-full flex items-end" style={{ height: '48px' }}>
                              <div className="w-full rounded-t"
                                style={{ height: `${Math.max((day.count / maxVal) * 48, day.count > 0 ? 6 : 2)}px`, backgroundColor: day.count > 0 ? '#6366f1' : '#e5e7eb' }}
                                title={`${day.date}: ${day.count} bookings`} />
                            </div>
                            <span className="text-xs text-gray-400">{day.label}</span>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                </div>

                {/* Recent Activities — compact, max 7, with View All */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
                  <div className="flex justify-between items-center mb-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase">Recent Activities</p>
                    {(dashboardStats.recent_activities || []).length > 7 && (
                      <button onClick={() => setCurrentView('admin-bookings')}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">
                        View All →
                      </button>
                    )}
                  </div>
                  {(dashboardStats.recent_activities || []).length === 0 ? (
                    <p className="text-gray-400 text-xs">No recent activity</p>
                  ) : (
                    <div className="divide-y divide-gray-50">
                      {(dashboardStats.recent_activities || []).slice(0, 7).map((activity, i) => (
                        <div key={i} className="flex items-center gap-2 py-1.5">
                          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                            activity.type === 'confirmed' ? 'bg-green-500' :
                            activity.type === 'cancelled' ? 'bg-red-400' :
                            activity.type === 'refunded' ? 'bg-blue-500' :
                            activity.type === 'club_added' ? 'bg-purple-500' :
                            activity.type === 'sport_added' ? 'bg-orange-400' :
                            'bg-yellow-400'
                          }`} />
                          <p className="text-xs text-gray-700 flex-1 truncate">{activity.message}</p>
                          <span className="text-xs text-gray-400 flex-shrink-0">{activity.time}</span>
                          {activity.amount && (
                            <span className={`text-xs font-semibold flex-shrink-0 ${activity.type === 'refunded' ? 'text-red-500' : 'text-green-600'}`}>
                              {activity.type === 'refunded' ? '-' : '+'}₹{activity.amount}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Admin - All Bookings */}
        {currentView === 'admin-bookings' && user?.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">All Bookings</h2>

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-5 flex-wrap">
              {['all', 'confirmed', 'pending', 'cancelled', 'refunded'].map(tab => {
                const count = tab === 'all' ? allBookings.length : allBookings.filter(b => b.status === tab).length;
                return (
                  <button key={tab} onClick={() => setAdminBookingFilter(tab)}
                    className={`px-4 py-2 rounded-full text-sm font-medium capitalize transition ${
                      adminBookingFilter === tab ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
                    }`}>
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    <span className="ml-1 text-xs opacity-80">({count})</span>
                  </button>
                );
              })}
            </div>

            {(() => {
              const filtered = adminBookingFilter === 'all'
                ? allBookings
                : allBookings.filter(b => b.status === adminBookingFilter);

              return filtered.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No {adminBookingFilter === 'all' ? '' : adminBookingFilter} bookings yet</p>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Club / Sport</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date & Time</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment Mode</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {filtered.map((booking) => (
                          <tr key={booking.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-800">{booking.user_name}</td>
                            <td className="px-4 py-3 text-sm">
                              <div className="font-medium text-gray-800">{booking.club_name}</div>
                              <div className="text-gray-500 text-xs">{booking.sport_name}</div>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className="text-gray-800">{booking.date}</div>
                              <div className="text-gray-500 text-xs">{booking.start_time} – {booking.end_time}</div>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className={`font-semibold ${booking.status === 'refunded' ? 'text-red-500' : 'text-gray-800'}`}>
                                ₹{booking.amount}
                              </div>
                              {booking.status === 'refunded' && (
                                <div className="text-xs text-blue-600 mt-0.5">↩ Refund to original payment</div>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {booking.payment_method ? (
                                <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                                  booking.payment_method === 'card' ? 'bg-purple-100 text-purple-700' :
                                  booking.payment_method === 'upi' ? 'bg-green-100 text-green-700' :
                                  booking.payment_method === 'netbanking' ? 'bg-blue-100 text-blue-700' :
                                  booking.payment_method === 'wallet' ? 'bg-orange-100 text-orange-700' :
                                  'bg-gray-100 text-gray-600'
                                }`}>
                                  {booking.payment_method === 'card' ? '💳 Card' :
                                   booking.payment_method === 'upi' ? '📱 UPI' :
                                   booking.payment_method === 'netbanking' ? '🏦 NetBanking' :
                                   booking.payment_method === 'wallet' ? '👛 Wallet' :
                                   booking.payment_method}
                                </span>
                              ) : (
                                <span className="text-gray-400 text-xs">—</span>
                              )}
                            </td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                                booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                                booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                booking.status === 'refunded' ? 'bg-blue-100 text-blue-800' :
                                booking.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {booking.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {booking.status === 'pending' && (
                                <div className="flex gap-2">
                                  <button onClick={() => handleUpdateBookingStatus(booking.id, 'confirmed')}
                                    className="text-green-600 hover:text-green-800" title="Confirm">
                                    <CheckCircle className="w-5 h-5" />
                                  </button>
                                  <button onClick={() => handleUpdateBookingStatus(booking.id, 'cancelled')}
                                    className="text-red-500 hover:text-red-700" title="Cancel">
                                    <XCircle className="w-5 h-5" />
                                  </button>
                                </div>
                              )}
                              {booking.status === 'refunded' && (
                                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                  Refund processed
                                </span>
                              )}
                              {booking.status === 'cancelled' && (
                                <span className="text-xs text-gray-400">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Admin - Manage Clubs */}
        {currentView === 'admin-clubs' && user?.is_staff && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-800">Manage Clubs</h2>
              <button
                onClick={() => {
                  setShowClubForm(true);
                  setEditingClub(null);
                  setClubFormData({ name: '', location: '', opening_time: '', closing_time: '', description: '', phone_number: '' });
                }}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <Plus className="w-5 h-5" />
                Add Club
              </button>
            </div>

            {showClubForm && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center text-sm font-bold">1</div>
                  <h3 className="text-xl font-bold">{editingClub ? 'Edit Club Details' : 'Add New Club'}</h3>
                </div>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Club Name <span className="text-red-500">*</span></label>
                      <input type="text" value={clubFormData.name}
                        onChange={(e) => setClubFormData({ ...clubFormData, name: e.target.value })}
                        placeholder="e.g. Green Valley Sports Club"
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Location <span className="text-red-500">*</span></label>
                      <input type="text" value={clubFormData.location}
                        onChange={(e) => setClubFormData({ ...clubFormData, location: e.target.value })}
                        placeholder="e.g. HSR Layout, Bengaluru"
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Opening Time <span className="text-red-500">*</span></label>
                      <input type="time" value={clubFormData.opening_time}
                        onChange={(e) => setClubFormData({ ...clubFormData, opening_time: e.target.value })}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Closing Time <span className="text-red-500">*</span></label>
                      <input type="time" value={clubFormData.closing_time}
                        onChange={(e) => setClubFormData({ ...clubFormData, closing_time: e.target.value })}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Description</label>
                    <textarea value={clubFormData.description}
                      onChange={(e) => setClubFormData({ ...clubFormData, description: e.target.value })}
                      placeholder="Describe your club facilities, amenities, etc."
                      className="w-full px-3 py-2 border rounded-lg text-sm" rows="2" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Contact Phone Number</label>
                    <input type="tel" value={clubFormData.phone_number}
                      onChange={(e) => setClubFormData({ ...clubFormData, phone_number: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                      placeholder="e.g. 9876543210"
                      className="w-full px-3 py-2 border rounded-lg text-sm"
                      maxLength="10" />
                  </div>

                  {!editingClub && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                      💡 After saving club details, you'll be prompted to add sports and pricing.
                    </div>
                  )}

                  <div className="flex gap-3">
                    <button onClick={handleSaveClub}
                      className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium">
                      {editingClub ? 'Update Club' : 'Save & Add Sports →'}
                    </button>
                    <button onClick={() => { setShowClubForm(false); setEditingClub(null); }}
                      className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {clubs.map((club) => (
                <div key={club.id} className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-1">{club.name}</h3>
                  <div className="space-y-1 text-sm text-gray-600 mb-3">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      <span>{club.location}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>{club.opening_time} - {club.closing_time}</span>
                    </div>
                    {club.sports && club.sports.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {club.sports.map(s => (
                          <span key={s.id} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs rounded-full">
                            {s.name} — ₹{s.price_per_hour}/hr
                          </span>
                        ))}
                      </div>
                    )}
                    {(!club.sports || club.sports.length === 0) && (
                      <p className="text-xs text-orange-500 mt-1">⚠ No sports added yet</p>
                    )}
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => {
                        setManagingSportsFor(club);
                        loadClubSports(club.id);
                        setShowSportForm(false);
                        setEditingSport(null);
                        setSportFormData({ name: '', price_per_hour: '', description: '', is_active: true });
                      }}
                      className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                    >
                      <Plus className="w-4 h-4" /> Sports
                    </button>
                    <button
                      onClick={() => {
                        setEditingClub(club);
                        setClubFormData({
                          name: club.name,
                          location: club.location,
                          opening_time: club.opening_time,
                          closing_time: club.closing_time,
                          description: club.description || '',
                          phone_number: club.phone_number || ''
                        });
                        setShowClubForm(true);
                      }}
                      className="flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteClub(club.id)}
                      className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sports Management Modal */}
        {managingSportsFor && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl mt-10 mb-10">
              <div className="flex justify-between items-center p-6 border-b">
                <div>
                  <h3 className="text-xl font-bold text-gray-800">Manage Sports</h3>
                  <p className="text-sm text-gray-500">{managingSportsFor.name}</p>
                </div>
                <button onClick={() => { setManagingSportsFor(null); setShowSportForm(false); }}
                  className="text-gray-400 hover:text-gray-600 text-2xl leading-none">✕</button>
              </div>

              <div className="p-6">
                {/* Existing Sports */}
                {clubSports.length > 0 ? (
                  <div className="mb-5">
                    <h4 className="text-sm font-semibold text-gray-600 mb-3 uppercase">Available Sports</h4>
                    <div className="space-y-2">
                      {clubSports.map(sport => (
                        <div key={sport.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3">
                          <div>
                            <span className="font-medium text-gray-800">{sport.name}</span>
                            <span className="ml-3 text-sm text-gray-500">₹{sport.price_per_hour}/hr</span>
                            {sport.description && <span className="ml-2 text-xs text-gray-400">{sport.description}</span>}
                            <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${sport.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {sport.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => {
                              setEditingSport(sport);
                              setSportFormData({ name: sport.name, price_per_hour: sport.price_per_hour, description: sport.description || '', is_active: sport.is_active });
                              setShowSportForm(true);
                            }} className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                            <button onClick={() => handleDeleteSport(sport.id)}
                              className="text-red-500 hover:text-red-700 text-sm">Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-400 mb-4">
                    <p>No sports added yet. Add your first sport below.</p>
                  </div>
                )}

                {/* Add/Edit Sport Form */}
                {!showSportForm ? (
                  <button onClick={() => { setShowSportForm(true); setEditingSport(null); setSportFormData({ name: '', price_per_hour: '', description: '', is_active: true }); }}
                    className="w-full py-2 border-2 border-dashed border-indigo-300 text-indigo-600 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 text-sm font-medium">
                    + Add New Sport
                  </button>
                ) : (
                  <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50">
                    <h4 className="font-semibold text-gray-700 mb-3">{editingSport ? 'Edit Sport' : 'Add New Sport'}</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">Sport Name <span className="text-red-500">*</span></label>
                        <select
                          value={sportFormData.name}
                          onChange={e => setSportFormData({ ...sportFormData, name: e.target.value })}
                          className="w-full px-3 py-2 border rounded-lg text-sm bg-white"
                        >
                          <option value="">Select a sport...</option>
                          {SPORT_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                          <option value="__custom__">Other (type below)</option>
                        </select>
                        {sportFormData.name === '__custom__' && (
                          <input type="text" placeholder="Enter sport name"
                            onChange={e => setSportFormData({ ...sportFormData, name: e.target.value })}
                            className="w-full mt-2 px-3 py-2 border rounded-lg text-sm" />
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium mb-1">Price per Hour (₹) <span className="text-red-500">*</span></label>
                          <input type="number" min="0" value={sportFormData.price_per_hour}
                            onChange={e => setSportFormData({ ...sportFormData, price_per_hour: e.target.value })}
                            placeholder="500" className="w-full px-3 py-2 border rounded-lg text-sm" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Status</label>
                          <select value={sportFormData.is_active}
                            onChange={e => setSportFormData({ ...sportFormData, is_active: e.target.value === 'true' })}
                            className="w-full px-3 py-2 border rounded-lg text-sm bg-white">
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                          </select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Description (optional)</label>
                        <input type="text" value={sportFormData.description}
                          onChange={e => setSportFormData({ ...sportFormData, description: e.target.value })}
                          placeholder="e.g. Indoor court, equipment provided"
                          className="w-full px-3 py-2 border rounded-lg text-sm" />
                      </div>
                      <div className="flex gap-2">
                        <button onClick={handleSaveSport}
                          className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium">
                          {editingSport ? 'Update Sport' : 'Add Sport'}
                        </button>
                        <button onClick={() => { setShowSportForm(false); setEditingSport(null); }}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Booking Confirmation Screen */}
        {currentView === 'booking-confirmed' && bookingConfirmation && (
          <div className="max-w-2xl mx-auto">
            {/* Celebration Header */}
            <div className="text-center mb-6">
              <div className="text-6xl mb-3">🎉</div>
              <h2 className="text-3xl font-bold text-gray-800">Booking Confirmed!</h2>
              <p className="text-gray-500 mt-1">Your slot has been successfully reserved.</p>
            </div>

            {/* Welcome + Confirmation Card */}
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              {/* Green Header Banner */}
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-5 text-white">
                <p className="text-indigo-200 text-sm font-medium">Welcome back,</p>
                <h3 className="text-2xl font-bold mt-0.5">
                  {bookingConfirmation.user?.first_name
                    ? `${bookingConfirmation.user.first_name} ${bookingConfirmation.user.last_name || ''}`.trim()
                    : bookingConfirmation.user?.username}
                </h3>
                <p className="text-indigo-200 text-sm mt-1">Confirmed on {bookingConfirmation.confirmedAt}</p>
              </div>

              {/* Club Info */}
              <div className="px-6 py-5 border-b border-gray-100">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-gray-400 uppercase font-semibold tracking-wide mb-1">Sports Club</p>
                    <h4 className="text-xl font-bold text-gray-800">{bookingConfirmation.club?.name}</h4>
                    <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                      <MapPin className="w-4 h-4" />
                      <span>{bookingConfirmation.club?.location}</span>
                    </div>
                  </div>
                  <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold">
                    ✓ Confirmed
                  </div>
                </div>
                {bookingConfirmation.club?.description && (
                  <p className="text-sm text-gray-600 mt-3 bg-gray-50 rounded-lg px-3 py-2">
                    {bookingConfirmation.club.description}
                  </p>
                )}
                {bookingConfirmation.club?.phone_number && (
                  <div className="flex items-center gap-2 mt-3 text-sm text-gray-600">
                    <span className="text-lg">📞</span>
                    <span className="font-medium">{bookingConfirmation.club.phone_number}</span>
                    <span className="text-gray-400">— Club Contact</span>
                  </div>
                )}
              </div>

              {/* Booking Details Grid */}
              <div className="px-6 py-5">
                <p className="text-xs text-gray-400 uppercase font-semibold tracking-wide mb-3">Booking Details</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-indigo-50 rounded-xl p-4">
                    <p className="text-xs text-indigo-400 font-medium mb-1">Sport</p>
                    <p className="text-lg font-bold text-indigo-700">
                      {bookingConfirmation.booking?.sport_name || bookingConfirmation.slot?.sport_name || '—'}
                    </p>
                  </div>
                  <div className="bg-purple-50 rounded-xl p-4">
                    <p className="text-xs text-purple-400 font-medium mb-1">Date</p>
                    <p className="text-lg font-bold text-purple-700">
                      {bookingConfirmation.booking?.date
                        ? new Date(bookingConfirmation.booking.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                        : '—'}
                    </p>
                  </div>
                  <div className="bg-green-50 rounded-xl p-4">
                    <p className="text-xs text-green-400 font-medium mb-1">Time Slot</p>
                    <p className="text-lg font-bold text-green-700">
                      {bookingConfirmation.booking?.start_time?.slice(0, 5)} – {bookingConfirmation.booking?.end_time?.slice(0, 5)}
                    </p>
                  </div>
                  <div className="bg-yellow-50 rounded-xl p-4">
                    <p className="text-xs text-yellow-500 font-medium mb-1">Amount Paid</p>
                    <p className="text-lg font-bold text-yellow-700">₹{bookingConfirmation.booking?.amount}</p>
                  </div>
                </div>

                {/* Payment Mode */}
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
                  <span>
                    {bookingConfirmation.paymentMode === 'card' ? '💳' :
                     bookingConfirmation.paymentMode === 'upi' ? '📱' :
                     bookingConfirmation.paymentMode === 'netbanking' ? '🏦' : '👛'}
                  </span>
                  <span>Paid via <strong className="text-gray-700 capitalize">{bookingConfirmation.paymentMode}</strong></span>
                </div>
              </div>

              {/* Important Note */}
              <div className="mx-6 mb-5 bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p className="text-sm font-semibold text-amber-800 mb-1">📋 Before you arrive</p>
                <ul className="text-sm text-amber-700 space-y-1">
                  <li>• Please arrive 15 minutes early</li>
                  <li>• Carry a valid photo ID for verification</li>
                  <li>• Wear appropriate sports attire</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="px-6 pb-6 flex gap-3">
                <button
                  onClick={() => {
                    setCurrentView('bookings');
                    setBookingConfirmation(null);
                  }}
                  className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition"
                >
                  View My Bookings
                </button>
                <button
                  onClick={() => {
                    setCurrentView('clubs');
                    setBookingConfirmation(null);
                  }}
                  className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition"
                >
                  Book Another Slot
                </button>
              </div>
            </div>
          </div>
        )}

        {/* User - Clubs View */}
        {currentView === 'clubs' && !user?.is_staff && (
          <div>
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Available Clubs</h2>
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search clubs by name or location..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {selectedClub ? (
              <div>
                <button
                  onClick={() => {
                    setSelectedClub(null);
                    setShowReviewForm(false);
                  }}
                  className="mb-4 text-indigo-600 hover:text-indigo-800"
                >
                  ← Back to Clubs
                </button>

                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                  <h3 className="text-2xl font-bold text-gray-800 mb-4">{selectedClub.name}</h3>
                  <div className="space-y-3 text-gray-600 mb-6">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-5 h-5" />
                      <span>{selectedClub.location}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-5 h-5" />
                      <span>{selectedClub.opening_time} - {selectedClub.closing_time}</span>
                    </div>
                    {selectedClub.average_rating && (
                      <div className="flex items-center gap-2">
                        <StarRating rating={selectedClub.average_rating} readonly />
                        <span className="text-sm">({selectedClub.total_reviews} reviews)</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => setCurrentView('book-slot')}
                    className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 mb-4"
                  >
                    Book Now
                  </button>

                  <button
                    onClick={() => {
                      setShowReviewForm(!showReviewForm);
                      if (!showReviewForm) loadClubReviews(selectedClub.id);
                    }}
                    className="w-full border border-indigo-600 text-indigo-600 py-2 rounded-lg hover:bg-indigo-50"
                  >
                    {showReviewForm ? 'Hide Reviews' : 'View Reviews & Rate'}
                  </button>
                </div>

                {showReviewForm && (
                  <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h4 className="text-xl font-bold mb-4">Write a Review</h4>
                    <div className="mb-4">
                      <label className="block text-sm font-medium mb-2">Your Rating</label>
                      <StarRating rating={reviewRating} onRatingChange={setReviewRating} />
                    </div>
                    <div className="mb-4">
                      <label className="block text-sm font-medium mb-2">Your Review</label>
                      <textarea
                        value={reviewText}
                        onChange={(e) => setReviewText(e.target.value)}
                        className="w-full px-4 py-2 border rounded-lg"
                        rows="4"
                        placeholder="Share your experience..."
                      />
                    </div>
                    <button
                      onClick={handleAddReview}
                      className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Submit Review
                    </button>

                    {clubReviews.length > 0 && (
                      <div className="mt-6">
                        <h4 className="text-lg font-bold mb-4">Customer Reviews</h4>
                        <div className="space-y-4">
                          {clubReviews.map((review) => (
                            <div key={review.id} className="border-b pb-4">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <p className="font-semibold">{review.user_name}</p>
                                  <StarRating rating={review.rating} readonly />
                                </div>
                                <span className="text-sm text-gray-500">{new Date(review.created_at).toLocaleDateString()}</span>
                              </div>
                              <p className="text-gray-700">{review.comment}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : clubs.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No clubs available yet</p>
              </div>
            ) : filteredClubs.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow-md">
                <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">We're not in "{searchTerm}" yet</h3>
                <p className="text-gray-500 mb-4 max-w-sm mx-auto">
                  Sorry, we don't have any sports clubs available at this location currently.
                  We're expanding soon — check back later!
                </p>
                <button
                  onClick={() => setSearchTerm('')}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
                >
                  View All Clubs
                </button>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredClubs.map((club) => (
                  <div key={club.id} className="bg-white rounded-lg shadow-md hover:shadow-xl transition p-6">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">{club.name}</h3>
                    <div className="space-y-2 text-sm text-gray-600 mb-4">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        <span>{club.location}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{club.opening_time} - {club.closing_time}</span>
                      </div>
                      {club.average_rating && (
                        <div className="flex items-center gap-2">
                          <StarRating rating={club.average_rating} readonly />
                          <span className="text-xs">({club.total_reviews})</span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setSelectedClub(club);
                        loadClubReviews(club.id);
                        setBookingForm(prev => ({ ...prev, club: club.id, sport: null }));
                      }}
                      className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition"
                    >
                      View Details
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Book Slot View */}
        {currentView === 'book-slot' && selectedClub && (
          <div>
            <button
              onClick={() => setCurrentView('clubs')}
              className="mb-4 text-indigo-600 hover:text-indigo-800"
            >
              ← Back to Club Details
            </button>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-2xl font-bold mb-6">Book Your Slot</h3>

              {lockedSlot && (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-400 rounded-lg flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-yellow-800">Slot Reserved</p>
                    <p className="text-sm text-yellow-700">Complete payment within 10 minutes or slot will be released</p>
                  </div>
                </div>
              )}

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Select Sport</label>
                  <select
                    className="w-full px-4 py-2 border rounded-lg"
                    onChange={(e) => {
                      setBookingForm({ ...bookingForm, sport: e.target.value });
                      if (bookingForm.club && bookingForm.date) {
                        loadAvailableSlots(bookingForm.club, e.target.value, bookingForm.date);
                      }
                    }}
                  >
                    <option value="">Choose a sport</option>
                    {selectedClub.sports?.map(sport => (
                      <option key={sport.id} value={sport.id}>{sport.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Select Date
                    <span className="text-xs text-gray-400 ml-2">(up to 15 days ahead)</span>
                  </label>
                  <input
                    type="date"
                    value={bookingForm.date}
                    min={new Date().toISOString().split('T')[0]}
                    max={(() => { const d = new Date(); d.setDate(d.getDate() + 15); return d.toISOString().split('T')[0]; })()}
                    onChange={(e) => {
                      const selected = new Date(e.target.value);
                      const maxDate = new Date();
                      maxDate.setDate(maxDate.getDate() + 15);
                      if (selected > maxDate) {
                        setError('Bookings can only be made up to 15 days in advance.');
                        return;
                      }
                      setBookingForm({ ...bookingForm, date: e.target.value });
                      if (bookingForm.club && bookingForm.sport) {
                        loadAvailableSlots(bookingForm.club, bookingForm.sport, e.target.value);
                      }
                    }}
                    className="w-full px-4 py-2 border rounded-lg"
                  />
                </div>
              </div>

              {availableSlots.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">Available Time Slots</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {availableSlots.map((slot, index) => (
                      <button
                        key={index}
                        onClick={() => handleSlotSelection(slot)}
                        disabled={slot.is_locked || slot.is_booked || slot.is_past}
                        className={`p-3 rounded-lg border-2 transition ${
                          slot.is_past ? 'border-gray-200 bg-gray-50 text-gray-300 cursor-not-allowed' :
                          slot.is_booked ? 'border-red-300 bg-red-50 text-red-400 cursor-not-allowed' :
                          slot.is_locked ? 'border-yellow-300 bg-yellow-50 text-yellow-600 cursor-not-allowed' :
                          selectedSlot?.start_time === slot.start_time ? 'border-indigo-600 bg-indigo-50 text-indigo-700' :
                          'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50'
                        }`}
                      >
                        <div className="text-sm font-semibold">{slot.start_time}</div>
                        <div className="text-xs">{slot.end_time}</div>
                        {slot.is_past && (
                          <div className="mt-1 text-xs text-gray-300">Past</div>
                        )}
                        {!slot.is_past && slot.is_booked && (
                          <div className="mt-1 text-xs text-red-400">Booked</div>
                        )}
                        {slot.is_locked && !slot.is_past && (
                          <div className="mt-1 flex items-center justify-center gap-1">
                            <Lock className="w-3 h-3" />
                            <span className="text-xs">Waitlist</span>
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                  {selectedSlot && lockedSlot && (
                    <div className="mt-6">
                      <div className="bg-gray-50 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-600">Selected Slot:</p>
                        <p className="font-bold text-lg">{selectedSlot.start_time} - {selectedSlot.end_time}</p>
                        <p className="text-2xl font-bold text-indigo-600 mt-2">₹{selectedSlot.price}</p>
                      </div>
                      <button
                        onClick={handleCreateBooking}
                        className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700"
                      >
                        Proceed to Payment
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* User Bookings View */}
        {currentView === 'bookings' && !user?.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">My Bookings</h2>

            {/* Filter Tabs */}
            <div className="flex gap-2 mb-6 flex-wrap">
              {['all', 'confirmed', 'pending', 'cancelled', 'refunded'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setBookingFilter(tab)}
                  className={`px-4 py-2 rounded-full text-sm font-medium capitalize transition ${
                    bookingFilter === tab
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                  <span className="ml-1 text-xs">
                    ({tab === 'all' ? bookings.length : bookings.filter(b => b.status === tab).length})
                  </span>
                </button>
              ))}
            </div>

            {(() => {
              const filtered = bookingFilter === 'all' ? bookings : bookings.filter(b => b.status === bookingFilter);
              return filtered.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-lg shadow">
                  <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">
                    {bookingFilter === 'all' ? 'No bookings yet' : `No ${bookingFilter} bookings`}
                  </p>
                  <button
                    onClick={() => setCurrentView('clubs')}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                  >
                    Browse Clubs
                  </button>
                </div>
              ) : (
                <div className="space-y-5">
                  {filtered.map((booking) => (
                    <div key={booking.id} className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">

                      {/* Card Header — gradient based on status */}
                      <div className={`px-5 py-4 ${
                        booking.status === 'confirmed' ? 'bg-gradient-to-r from-indigo-600 to-purple-600' :
                        booking.status === 'pending' ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                        booking.status === 'refunded' ? 'bg-gradient-to-r from-blue-500 to-cyan-500' :
                        booking.status === 'cancelled' ? 'bg-gradient-to-r from-gray-400 to-gray-500' :
                        'bg-gradient-to-r from-indigo-500 to-purple-500'
                      } text-white`}>
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-white text-opacity-80 text-xs font-medium uppercase tracking-wide">
                              {booking.status === 'confirmed' ? '✓ Booking Confirmed' :
                               booking.status === 'pending' ? '⏳ Payment Pending' :
                               booking.status === 'refunded' ? '↩ Refund Processed' :
                               booking.status === 'cancelled' ? '✕ Booking Cancelled' : booking.status}
                            </p>
                            <h3 className="text-lg font-bold mt-0.5">{booking.club_name}</h3>
                            <p className="text-white text-sm opacity-80">{booking.sport_name}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-white text-opacity-70 text-xs">Amount</p>
                            <p className="text-xl font-bold">₹{booking.amount}</p>
                          </div>
                        </div>
                      </div>

                      {/* Booking Detail Tiles */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-0 divide-x divide-y sm:divide-y-0 divide-gray-100 border-b border-gray-100">
                        <div className="px-4 py-3 text-center">
                          <p className="text-xs text-gray-400 mb-0.5">Date</p>
                          <p className="text-sm font-bold text-gray-800">
                            {booking.date ? new Date(booking.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                          </p>
                        </div>
                        <div className="px-4 py-3 text-center">
                          <p className="text-xs text-gray-400 mb-0.5">Time Slot</p>
                          <p className="text-sm font-bold text-gray-800">
                            {booking.start_time?.slice(0,5)} – {booking.end_time?.slice(0,5)}
                          </p>
                        </div>
                        <div className="px-4 py-3 text-center">
                          <p className="text-xs text-gray-400 mb-0.5">Sport</p>
                          <p className="text-sm font-bold text-gray-800">{booking.sport_name}</p>
                        </div>
                        <div className="px-4 py-3 text-center">
                          <p className="text-xs text-gray-400 mb-0.5">Payment</p>
                          <p className="text-sm font-bold text-gray-800 capitalize">
                            {booking.payment_method
                              ? (booking.payment_method === 'card' ? '💳 Card' :
                                 booking.payment_method === 'upi' ? '📱 UPI' :
                                 booking.payment_method === 'netbanking' ? '🏦 NetBanking' :
                                 booking.payment_method === 'wallet' ? '👛 Wallet' :
                                 booking.payment_method)
                              : '—'}
                          </p>
                        </div>
                      </div>

                      {/* Club Info + Actions */}
                      <div className="px-5 py-4">
                        <div className="flex items-center gap-1 text-xs text-gray-500 mb-3">
                          <MapPin className="w-3 h-3" />
                          <span>{booking.club_location || booking.club_name}</span>
                        </div>

                        {/* Confirmed — before-you-arrive note + cancel */}
                        {booking.status === 'confirmed' && (
                          <div className="space-y-3">
                            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                              <p className="text-xs font-semibold text-amber-700 mb-1">📋 Before you arrive</p>
                              <ul className="text-xs text-amber-600 space-y-0.5">
                                <li>• Arrive 15 minutes early</li>
                                <li>• Carry a valid photo ID</li>
                                <li>• Wear appropriate sports attire</li>
                              </ul>
                            </div>
                            <button
                              onClick={() => handleCancelBooking(booking)}
                              className="w-full px-4 py-2.5 border border-red-400 text-red-500 rounded-xl hover:bg-red-50 text-sm font-medium transition"
                            >
                              Cancel Booking & Request Refund
                            </button>
                          </div>
                        )}

                        {/* Pending — pay or cancel */}
                        {booking.status === 'pending' && (
                          <div className="space-y-2">
                            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3 text-xs text-yellow-700">
                              ⚠ Complete payment to confirm your slot before it expires
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => { setPendingBooking(booking); setShowPayment(true); }}
                                className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 font-semibold text-sm"
                              >
                                Complete Payment — ₹{booking.amount}
                              </button>
                              <button
                                onClick={() => handleCancelBooking(booking)}
                                className="px-4 py-2.5 border border-red-400 text-red-500 rounded-xl hover:bg-red-50 text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Cancelled */}
                        {booking.status === 'cancelled' && (
                          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-600">
                            ✕ Booking cancelled — slot is now available for others
                          </div>
                        )}

                        {/* Refunded */}
                        {booking.status === 'refunded' && (
                          <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700">
                            ↩ Refund of <strong>₹{booking.amount}</strong> will be credited to your original payment method within 5–7 business days
                          </div>
                        )}

                        {/* Review for completed */}
                        {booking.status === 'completed' && !booking.has_review && (
                          <button
                            onClick={() => {
                              setSelectedClub({ id: booking.club_id, name: booking.club_name });
                              setShowReviewForm(true);
                              setCurrentView('clubs');
                            }}
                            className="w-full px-4 py-2.5 border border-indigo-500 text-indigo-600 rounded-xl hover:bg-indigo-50 text-sm font-medium"
                          >
                            ⭐ Rate This Experience
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
        )}


        {/* Waitlist View */}
        {currentView === 'waitlist' && !user?.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">My Waitlist</h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-blue-900 mb-1">About Waitlist</h3>
                  <p className="text-sm text-blue-800">
                    You'll be automatically notified via SMS and Email when any of these slots become available.
                    The slot becomes available when the previous user's 10-minute lock expires without payment.
                  </p>
                </div>
              </div>
            </div>

            {waitlistedSlots.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No slots in waitlist</p>
                <button
                  onClick={() => setCurrentView('clubs')}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                  Browse Clubs
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {waitlistedSlots.map((waitlist) => (
                  <div key={waitlist.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">{waitlist.club_name}</h3>
                        <p className="text-gray-600">{waitlist.sport_name}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${waitlist.notified
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                        }`}>
                        {waitlist.notified ? 'Notified' : 'Waiting'}
                      </span>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600 mb-4">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{waitlist.date}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{waitlist.start_time} - {waitlist.end_time}</span>
                      </div>
                    </div>

                    {waitlist.notified && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                        <p className="text-sm text-green-800 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          This slot is now available! Book it before someone else does.
                        </p>
                      </div>
                    )}

                    <div className="flex gap-3">
                      {waitlist.notified ? (
                        <button
                          onClick={() => {
                            // Navigate to booking for this slot
                            setSelectedClub({ id: waitlist.club });
                            setBookingForm({
                              club: waitlist.club,
                              sport: waitlist.sport,
                              date: waitlist.date,
                              slot: null
                            });
                            setCurrentView('book-slot');
                          }}
                          className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition"
                        >
                          Book Now
                        </button>
                      ) : (
                        <div className="flex-1 bg-gray-100 text-gray-500 py-2 rounded-lg text-center">
                          Waiting for slot to be available...
                        </div>
                      )}

                      <button
                        onClick={() => handleRemoveFromWaitlist(waitlist.id)}
                        className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition"
                      >
                        Remove
                      </button>
                    </div>

                    <p className="text-xs text-gray-500 mt-3">
                      Added to waitlist: {new Date(waitlist.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {/* Profile View */}
        {currentView === 'profile' && user && !user.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">My Profile</h2>
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-20 h-20 bg-indigo-600 rounded-full flex items-center justify-center">
                  <User className="w-10 h-10 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-800">
                    {user.first_name} {user.last_name}
                  </h3>
                  <p className="text-gray-600">@{user.username}</p>
                </div>
              </div>
              <div className="space-y-3 text-gray-700">
                <div className="flex justify-between py-2 border-b">
                  <span className="font-semibold">Email:</span>
                  <span>{user.email}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="font-semibold">Mobile:</span>
                  <span>{user.mobile_number}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="font-semibold">Member Since:</span>
                  <span>{user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="font-semibold">Total Bookings:</span>
                  <span>{bookings.length}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="font-semibold">Notifications:</span>
                  <span className="text-green-600">✓ SMS & Email Enabled</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;