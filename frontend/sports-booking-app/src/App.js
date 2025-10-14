import React, { useState, useEffect } from 'react';
import { AlertCircle, Calendar, Clock, MapPin, User, LogOut, CreditCard, Search, Menu, X, Star, Users, TrendingUp, DollarSign, Plus, Edit, Trash2, Lock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

const api = {
  sendOTP: (mobile) => fetch(`${API_BASE_URL}/accounts/send-otp/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mobile_number: mobile })
  }),
  
  verifyOTP: (mobile, otp) => fetch(`${API_BASE_URL}/accounts/verify-otp/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mobile_number: mobile, otp })
  }),
  
  register: (userData) => fetch(`${API_BASE_URL}/accounts/register/`, {
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
    `${API_BASE_URL}/bookings/available-slots/?club=${clubId}&sport=${sportId}&date=${date}`,
    { headers: { 'Authorization': `Bearer ${token}` }}
  ),
  
  lockSlot: (token, slotData) => fetch(`${API_BASE_URL}/bookings/lock-slot/`, {
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
  
  getUserProfile: (token) => fetch(`${API_BASE_URL}/accounts/profile/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  
  // Admin APIs
  getDashboardStats: (token) => fetch(`${API_BASE_URL}/admin/dashboard-stats/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  
  getAllBookings: (token) => fetch(`${API_BASE_URL}/admin/bookings/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }),
  
  updateBookingStatus: (token, bookingId, status) => fetch(
    `${API_BASE_URL}/admin/bookings/${bookingId}/status/`,
    {
      method: 'PATCH',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status })
    }
  ),
  
  createClub: (token, clubData) => fetch(`${API_BASE_URL}/admin/clubs/`, {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(clubData)
  }),
  
  updateClub: (token, clubId, clubData) => fetch(`${API_BASE_URL}/admin/clubs/${clubId}/`, {
    method: 'PUT',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(clubData)
  }),
  
  deleteClub: (token, clubId) => fetch(`${API_BASE_URL}/admin/clubs/${clubId}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  })
};

// Stripe Mock Component (In production, use @stripe/react-stripe-js)
const StripePaymentForm = ({ amount, onSuccess, onCancel }) => {
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvc, setCvc] = useState('');
  const [processing, setProcessing] = useState(false);

  const handleSubmit = async () => {
    setProcessing(true);
    // Simulate payment processing
    setTimeout(() => {
      onSuccess({ paymentIntentId: 'pi_' + Math.random().toString(36).substr(2, 9) });
      setProcessing(false);
    }, 2000);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-xl font-bold mb-4">Payment Details</h3>
      <div className="mb-4">
        <p className="text-2xl font-bold text-indigo-600 mb-4">₹{amount}</p>
      </div>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Card Number</label>
          <input
            type="text"
            value={cardNumber}
            onChange={(e) => setCardNumber(e.target.value)}
            placeholder="4242 4242 4242 4242"
            className="w-full px-4 py-2 border rounded-lg"
            maxLength="19"
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Expiry Date</label>
            <input
              type="text"
              value={expiry}
              onChange={(e) => setExpiry(e.target.value)}
              placeholder="MM/YY"
              className="w-full px-4 py-2 border rounded-lg"
              maxLength="5"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">CVC</label>
            <input
              type="text"
              value={cvc}
              onChange={(e) => setCvc(e.target.value)}
              placeholder="123"
              className="w-full px-4 py-2 border rounded-lg"
              maxLength="3"
            />
          </div>
        </div>
      </div>
      
      <div className="flex gap-3 mt-6">
        <button
          onClick={handleSubmit}
          disabled={processing}
          className="flex-1 bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {processing ? 'Processing...' : 'Pay Now'}
        </button>
        <button
          onClick={onCancel}
          className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
      
      <p className="text-xs text-gray-500 mt-4 text-center">
        🔒 Secured by Stripe - Your payment information is encrypted
      </p>
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
          className={`w-6 h-6 ${
            star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
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
  
  const [mobile, setMobile] = useState('');
  const [otp, setOTP] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  
  const [regData, setRegData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    mobile_number: ''
  });
  
  const [clubs, setClubs] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [selectedClub, setSelectedClub] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [lockedSlot, setLockedSlot] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [pendingBooking, setPendingBooking] = useState(null);
  
  // Review state
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState('');
  const [clubReviews, setClubReviews] = useState([]);
  
  // Admin state
  const [dashboardStats, setDashboardStats] = useState(null);
  const [allBookings, setAllBookings] = useState([]);
  const [showClubForm, setShowClubForm] = useState(false);
  const [editingClub, setEditingClub] = useState(null);
  const [clubFormData, setClubFormData] = useState({
    name: '',
    location: '',
    opening_time: '',
    closing_time: '',
    description: ''
  });
  
  // Booking form state
  const [bookingForm, setBookingForm] = useState({
    club: null,
    sport: null,
    date: new Date().toISOString().split('T')[0],
    slot: null
  });
  
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);
  
  useEffect(() => {
    if (token) {
      loadUserData();
    }
  }, [token]);
  
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
  
  const loadUserData = async () => {
    try {
      const response = await api.getUserProfile(token);
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
    }
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
        setSuccess('OTP sent successfully! Check your SMS.');
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
    
    try {
      const response = await api.verifyOTP(mobile, otp);
      const data = await response.json();
      
      if (response.ok) {
        setIsVerified(true);
        setSuccess('OTP verified! Please complete registration.');
        setRegData({ ...regData, mobile_number: mobile });
        setCurrentView('register');
      } else {
        setError(data.error || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };
  
  const handleRegister = async () => {
    setError('');
    setSuccess('');
    
    if (!regData.username || !regData.email || !regData.first_name || !regData.last_name) {
      setError('Please fill all fields');
      return;
    }
    
    try {
      const response = await api.register(regData);
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access);
        localStorage.setItem('token', data.access);
        setSuccess('Registration successful! Welcome email sent.');
        loadUserData();
      } else {
        setError(data.error || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
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
  };
  
  const loadClubs = async () => {
    try {
      const response = await api.getClubs(token);
      if (response.ok) {
        const data = await response.json();
        setClubs(data);
      }
    } catch (err) {
      setError('Failed to load clubs');
    }
  };
  
  const loadBookings = async () => {
    try {
      const response = await api.getBookings(token);
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      }
    } catch (err) {
      setError('Failed to load bookings');
    }
  };
  
  const loadAvailableSlots = async (clubId, sportId, date) => {
    try {
      const response = await api.getAvailableSlots(token, clubId, sportId, date);
      if (response.ok) {
        const data = await response.json();
        setAvailableSlots(data);
      }
    } catch (err) {
      setError('Failed to load available slots');
    }
  };
  
  const handleSlotSelection = async (slot) => {
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
      
      if (response.ok) {
        const data = await response.json();
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
        
      } else {
        const data = await response.json();
        setError(data.error || 'Slot is no longer available');
        loadAvailableSlots(bookingForm.club, bookingForm.sport, bookingForm.date);
      }
    } catch (err) {
      setError('Failed to lock slot');
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
        payment_intent_id: paymentData.paymentIntentId
      });
      
      if (response.ok) {
        setSuccess('Booking confirmed! Confirmation sent via SMS and Email.');
        setShowPayment(false);
        setPendingBooking(null);
        setSelectedSlot(null);
        setLockedSlot(null);
        setCurrentView('bookings');
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
        setAllBookings(data);
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
    try {
      const response = editingClub
        ? await api.updateClub(token, editingClub.id, clubFormData)
        : await api.createClub(token, clubFormData);
      
      if (response.ok) {
        setSuccess(editingClub ? 'Club updated!' : 'Club created!');
        setShowClubForm(false);
        setEditingClub(null);
        setClubFormData({ name: '', location: '', opening_time: '', closing_time: '', description: '' });
        loadClubs();
      } else {
        setError('Failed to save club');
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
  
  useEffect(() => {
    if (token) {
      if (currentView === 'clubs') loadClubs();
      if (currentView === 'bookings') loadBookings();
      if (currentView === 'admin-dashboard' && user?.is_staff) {
        loadDashboardStats();
        loadClubs();
      }
      if (currentView === 'admin-bookings' && user?.is_staff) loadAllBookings();
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Enter OTP</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOTP(e.target.value)}
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
                onClick={() => { setOtpSent(false); setOTP(''); }}
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
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'admin-dashboard' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    Dashboard
                  </button>
                  <button
                    onClick={() => setCurrentView('admin-bookings')}
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'admin-bookings' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    All Bookings
                  </button>
                  <button
                    onClick={() => setCurrentView('admin-clubs')}
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'admin-clubs' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    Manage Clubs
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setCurrentView('clubs')}
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'clubs' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    Clubs
                  </button>
                  <button
                    onClick={() => setCurrentView('bookings')}
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'bookings' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    My Bookings
                  </button>
                  <button
                    onClick={() => setCurrentView('profile')}
                    className={`px-4 py-2 rounded-lg transition ${
                      currentView === 'profile' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
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
        
        {/* Admin Dashboard */}
        {currentView === 'admin-dashboard' && user?.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">Admin Dashboard</h2>
            
            {dashboardStats && (
              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-600 text-sm">Total Bookings</p>
                      <p className="text-3xl font-bold text-gray-800">{dashboardStats.total_bookings}</p>
                    </div>
                    <Calendar className="w-12 h-12 text-indigo-600" />
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-600 text-sm">Total Revenue</p>
                      <p className="text-3xl font-bold text-gray-800">₹{dashboardStats.total_revenue}</p>
                    </div>
                    <DollarSign className="w-12 h-12 text-green-600" />
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-600 text-sm">Active Users</p>
                      <p className="text-3xl font-bold text-gray-800">{dashboardStats.active_users}</p>
                    </div>
                    <Users className="w-12 h-12 text-blue-600" />
                  </div>
                </div>
                
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-600 text-sm">Today's Bookings</p>
                      <p className="text-3xl font-bold text-gray-800">{dashboardStats.today_bookings}</p>
                    </div>
                    <TrendingUp className="w-12 h-12 text-purple-600" />
                  </div>
                </div>
              </div>
            )}
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold mb-4">Recent Activity</h3>
              <p className="text-gray-600">All bookings and activities are managed in real-time with instant notifications.</p>
            </div>
          </div>
        )}
        
        {/* Admin - All Bookings */}
        {currentView === 'admin-bookings' && user?.is_staff && (
          <div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">All Bookings</h2>
            
            {allBookings.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No bookings yet</p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Club</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {allBookings.map((booking) => (
                        <tr key={booking.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{booking.user_name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{booking.club_name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{booking.date}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">{booking.start_time} - {booking.end_time}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">₹{booking.amount}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                              booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              booking.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {booking.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {booking.status === 'pending' && (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleUpdateBookingStatus(booking.id, 'confirmed')}
                                  className="text-green-600 hover:text-green-800"
                                  title="Confirm"
                                >
                                  <CheckCircle className="w-5 h-5" />
                                </button>
                                <button
                                  onClick={() => handleUpdateBookingStatus(booking.id, 'cancelled')}
                                  className="text-red-600 hover:text-red-800"
                                  title="Cancel"
                                >
                                  <XCircle className="w-5 h-5" />
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
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
                  setClubFormData({ name: '', location: '', opening_time: '', closing_time: '', description: '' });
                }}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                <Plus className="w-5 h-5" />
                Add Club
              </button>
            </div>
            
            {showClubForm && (
              <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <h3 className="text-xl font-bold mb-4">{editingClub ? 'Edit Club' : 'Add New Club'}</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Club Name</label>
                    <input
                      type="text"
                      value={clubFormData.name}
                      onChange={(e) => setClubFormData({ ...clubFormData, name: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Location</label>
                    <input
                      type="text"
                      value={clubFormData.location}
                      onChange={(e) => setClubFormData({ ...clubFormData, location: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Opening Time</label>
                      <input
                        type="time"
                        value={clubFormData.opening_time}
                        onChange={(e) => setClubFormData({ ...clubFormData, opening_time: e.target.value })}
                        className="w-full px-4 py-2 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Closing Time</label>
                      <input
                        type="time"
                        value={clubFormData.closing_time}
                        onChange={(e) => setClubFormData({ ...clubFormData, closing_time: e.target.value })}
                        className="w-full px-4 py-2 border rounded-lg"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Description</label>
                    <textarea
                      value={clubFormData.description}
                      onChange={(e) => setClubFormData({ ...clubFormData, description: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg"
                      rows="3"
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveClub}
                      className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setShowClubForm(false);
                        setEditingClub(null);
                      }}
                      className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {clubs.map((club) => (
                <div key={club.id} className="bg-white rounded-lg shadow-md p-6">
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
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingClub(club);
                        setClubFormData({
                          name: club.name,
                          location: club.location,
                          opening_time: club.opening_time,
                          closing_time: club.closing_time,
                          description: club.description || ''
                        });
                        setShowClubForm(true);
                      }}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <Edit className="w-4 h-4" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteClub(club.id)}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
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
                  <label className="block text-sm font-medium mb-2">Select Date</label>
                  <input
                    type="date"
                    value={bookingForm.date}
                    min={new Date().toISOString().split('T')[0]}
                    onChange={(e) => {
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
                        disabled={slot.is_locked || slot.is_booked}
                        className={`p-3 rounded-lg border-2 transition ${
                          slot.is_booked ? 'border-red-300 bg-red-50 text-red-400 cursor-not-allowed' :
                          slot.is_locked ? 'border-yellow-300 bg-yellow-50 text-yellow-600 cursor-not-allowed' :
                          selectedSlot?.start_time === slot.start_time ? 'border-indigo-600 bg-indigo-50 text-indigo-700' :
                          'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50'
                        }`}
                      >
                        <div className="text-sm font-semibold">{slot.start_time}</div>
                        <div className="text-xs">{slot.end_time}</div>
                        {slot.is_locked && <Lock className="w-3 h-3 mx-auto mt-1" />}
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
            {bookings.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No bookings yet</p>
                <button
                  onClick={() => setCurrentView('clubs')}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                  Browse Clubs
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {bookings.map((booking) => (
                  <div key={booking.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">{booking.club_name}</h3>
                        <p className="text-gray-600">{booking.sport_name}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        booking.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                        booking.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        booking.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {booking.status}
                      </span>
                    </div>
                    <div className="grid md:grid-cols-3 gap-4 text-sm text-gray-600 mb-4">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{booking.date}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>{booking.start_time} - {booking.end_time}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CreditCard className="w-4 h-4" />
                        <span>₹{booking.amount}</span>
                      </div>
                    </div>
                    {booking.status === 'confirmed' && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
                        ✓ Confirmation sent via SMS and Email
                      </div>
                    )}
                    {booking.status === 'completed' && !booking.has_review && (
                      <button
                        onClick={() => {
                          setSelectedClub({ id: booking.club_id, name: booking.club_name });
                          setShowReviewForm(true);
                          setCurrentView('clubs');
                        }}
                        className="mt-3 w-full px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50"
                      >
                        Rate This Experience
                      </button>
                    )}
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