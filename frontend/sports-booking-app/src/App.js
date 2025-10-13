import React, { useState, useEffect } from 'react';
import { Search, MapPin, Calendar, Clock, User, LogOut, ChevronRight, Phone, Loader2 } from 'lucide-react';

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// API Service
const api = {
  sendOTP: (phoneNumber) =>
    fetch(`${API_BASE_URL}/auth/send-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber })
    }),

  verifyOTP: (phoneNumber, otp) =>
    fetch(`${API_BASE_URL}/auth/verify-otp/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone_number: phoneNumber, otp })
    }),

  getAllClubs: (token) =>
    fetch(`${API_BASE_URL}/clubs/`, {
      headers: { 'Authorization': `Token ${token}` }
    }),

  getNearbyClubs: (lat, lng, radius, sport) =>
    fetch(`${API_BASE_URL}/clubs/nearby/?lat=${lat}&lng=${lng}&radius=${radius}&sport=${sport}`),

  getClubDetails: (clubId) =>
    fetch(`${API_BASE_URL}/clubs/${clubId}/`),

  getAvailableSlots: (clubId, date, sport) =>
    fetch(`${API_BASE_URL}/clubs/${clubId}/available_slots/?date=${date}&sport=${sport}`),

  createBooking: (token, bookingData) =>
    fetch(`${API_BASE_URL}/bookings/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(bookingData)
    }),

  getUpcomingBookings: (token) =>
    fetch(`${API_BASE_URL}/bookings/upcoming/`, {
      headers: { 'Authorization': `Token ${token}` }
    }),

  confirmPayment: (token, paymentId, paymentIntentId) =>
    fetch(`${API_BASE_URL}/payments/${paymentId}/confirm_payment/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ payment_intent_id: paymentIntentId })
    }),

  getPaymentStatus: (token, transactionId) =>
    fetch(`${API_BASE_URL}/payments/payment_status/?transaction_id=${transactionId}`, {
      headers: { 'Authorization': `Token ${token}` }
    })
};

export default function SportsClubBooking() {
  const [authToken, setAuthToken] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('authToken');
    }
    return null;
  });
  const [currentView, setCurrentView] = useState('home');

  useEffect(() => {
    if (authToken && typeof window !== 'undefined') {
      localStorage.setItem('authToken', authToken);
    }
  }, [authToken]);

  const handleLogout = () => {
    setAuthToken(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
    setCurrentView('home');
  };

  if (!authToken) {
    return <LoginScreen onLogin={setAuthToken} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onLogout={handleLogout} currentView={currentView} setCurrentView={setCurrentView} />
      <main className="max-w-7xl mx-auto px-4 py-8">
        {currentView === 'home' && <HomeView token={authToken} setCurrentView={setCurrentView} />}
        {currentView === 'bookings' && <BookingsView token={authToken} />}
        {currentView === 'clubs' && <ClubsView token={authToken} />}
      </main>
    </div>
  );
}

function Header({ onLogout, currentView, setCurrentView }) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-blue-600">SportBook</h1>
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('home')}
                className={`px-4 py-2 rounded-lg transition ${currentView === 'home' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                Home
              </button>
              <button
                onClick={() => setCurrentView('clubs')}
                className={`px-4 py-2 rounded-lg transition ${currentView === 'clubs' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                Clubs
              </button>
              <button
                onClick={() => setCurrentView('bookings')}
                className={`px-4 py-2 rounded-lg transition ${currentView === 'bookings' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                My Bookings
              </button>
            </nav>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}

function LoginScreen({ onLogin }) {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async () => {
    if (!phoneNumber) return;
    setLoading(true);
    setError('');

    try {
      const response = await api.sendOTP(phoneNumber);
      const data = await response.json();

      if (response.ok) {
        setOtpSent(true);
      } else {
        setError(data.message || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp) return;
    setLoading(true);
    setError('');

    try {
      const response = await api.verifyOTP(phoneNumber, otp);
      const data = await response.json();

      if (response.ok && data.token) {
        onLogin(data.token);
      } else {
        setError(data.message || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">SportBook</h1>
          <p className="text-gray-600">Book your favorite sports venues</p>
        </div>

        {!otpSent ? (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="Enter your phone number"
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handleSendOTP}
              disabled={loading || !phoneNumber}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Send OTP'}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter OTP
              </label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="Enter 6-digit OTP"
                maxLength="6"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest"
              />
              <p className="text-sm text-gray-500 mt-2">
                OTP sent to {phoneNumber}
              </p>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handleVerifyOTP}
              disabled={loading || !otp}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Verify OTP'}
            </button>

            <button
              onClick={() => {
                setOtpSent(false);
                setOtp('');
                setError('');
              }}
              className="w-full text-blue-600 hover:underline text-sm"
            >
              Change phone number
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function HomeView({ token }) {
  const [nearbyClubs, setNearbyClubs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({
    sport: 'football',
    radius: 10
  });

  const loadNearbyClubs = async () => {
    setLoading(true);
    try {
      const response = await api.getNearbyClubs(12.9716, 77.5946, searchParams.radius, searchParams.sport);
      const data = await response.json();
      setNearbyClubs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading clubs:', err);
      setNearbyClubs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNearbyClubs();
  }, []);

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Find Nearby Clubs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={searchParams.sport}
            onChange={(e) => setSearchParams({ ...searchParams, sport: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="football">Football</option>
            <option value="cricket">Cricket</option>
            <option value="tennis">Tennis</option>
            <option value="badminton">Badminton</option>
          </select>
          <select
            value={searchParams.radius}
            onChange={(e) => setSearchParams({ ...searchParams, radius: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="5">Within 5 km</option>
            <option value="10">Within 10 km</option>
            <option value="20">Within 20 km</option>
            <option value="50">Within 50 km</option>
          </select>
          <button
            onClick={loadNearbyClubs}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center transition"
          >
            <Search className="w-4 h-4 mr-2" />
            Search
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {nearbyClubs.map((club) => (
            <ClubCard key={club.id} club={club} token={token} />
          ))}
        </div>
      )}

      {!loading && nearbyClubs.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No clubs found. Try adjusting your search filters.
        </div>
      )}
    </div>
  );
}

function ClubCard({ club, token }) {
  const [showBooking, setShowBooking] = useState(false);

  return (
    <>
      <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden">
        <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-500"></div>
        <div className="p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-2">{club.name}</h3>
          <div className="flex items-start space-x-2 text-gray-600 mb-4">
            <MapPin className="w-4 h-4 mt-1 flex-shrink-0" />
            <span className="text-sm">{club.address || 'Address not available'}</span>
          </div>
          {club.distance && (
            <p className="text-sm text-gray-500 mb-4">
              {club.distance.toFixed(1)} km away
            </p>
          )}
          <button
            onClick={() => setShowBooking(true)}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center transition"
          >
            Book Now
            <ChevronRight className="w-4 h-4 ml-2" />
          </button>
        </div>
      </div>

      {showBooking && (
        <BookingModal
          club={club}
          token={token}
          onClose={() => setShowBooking(false)}
        />
      )}
    </>
  );
}

function BookingModal({ club, token, onClose }) {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSport, setSelectedSport] = useState('football');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [specialRequests, setSpecialRequests] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const loadSlots = async () => {
    setLoading(true);
    try {
      const response = await api.getAvailableSlots(club.id, selectedDate, selectedSport);
      const data = await response.json();
      setAvailableSlots(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading slots:', err);
      setAvailableSlots([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSlots();
  }, [selectedDate, selectedSport]);

  const handleBooking = async () => {
    if (!selectedSlot) return;

    setLoading(true);
    try {
      const response = await api.createBooking(token, {
        club: club.id,
        time_slot: selectedSlot.id,
        special_requests: specialRequests
      });

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => onClose(), 2000);
      }
    } catch (err) {
      console.error('Error creating booking:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-800">Book at {club.name}</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
              ✕
            </button>
          </div>
        </div>

        {success ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Booking Confirmed!</h3>
            <p className="text-gray-600">Your booking has been successfully created.</p>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sport</label>
                <select
                  value={selectedSport}
                  onChange={(e) => setSelectedSport(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="football">Football</option>
                  <option value="cricket">Cricket</option>
                  <option value="tennis">Tennis</option>
                  <option value="badminton">Badminton</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Available Time Slots</label>
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                </div>
              ) : availableSlots.length > 0 ? (
                <div className="grid grid-cols-3 gap-3">
                  {availableSlots.map((slot) => (
                    <button
                      key={slot.id}
                      onClick={() => setSelectedSlot(slot)}
                      className={`p-3 border rounded-lg text-sm transition ${selectedSlot?.id === slot.id
                        ? 'border-blue-600 bg-blue-50 text-blue-600'
                        : 'border-gray-300 hover:border-blue-300'
                        }`}
                    >
                      <Clock className="w-4 h-4 mx-auto mb-1" />
                      {slot.start_time} - {slot.end_time}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-4">No slots available for selected date and sport</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Special Requests (Optional)</label>
              <textarea
                value={specialRequests}
                onChange={(e) => setSpecialRequests(e.target.value)}
                placeholder="e.g., Please reserve parking spot"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                rows="3"
              />
            </div>

            <button
              onClick={handleBooking}
              disabled={!selectedSlot || loading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Processing...' : 'Confirm Booking'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function BookingsView({ token }) {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadBookings = async () => {
      try {
        const response = await api.getUpcomingBookings(token);
        const data = await response.json();
        setBookings(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error loading bookings:', err);
        setBookings([]);
      } finally {
        setLoading(false);
      }
    };

    loadBookings();
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">My Bookings</h2>

      {bookings.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No bookings yet</h3>
          <p className="text-gray-600">Start by booking your favorite sports venue!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <div key={booking.id} className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    {booking.club_name || `Club #${booking.club}`}
                  </h3>
                  <div className="space-y-1 text-sm text-gray-600">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2" />
                      {booking.date || 'Date not available'}
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      {booking.time || 'Time not available'}
                    </div>
                    {booking.special_requests && (
                      <div className="mt-2 p-2 bg-gray-50 rounded">
                        <span className="font-medium">Special Requests:</span> {booking.special_requests}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                    booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                    {booking.status || 'Pending'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ClubsView({ token }) {
  const [clubs, setClubs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadClubs = async () => {
      try {
        const response = await api.getAllClubs(token);
        const data = await response.json();
        setClubs(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Error loading clubs:', err);
        setClubs([]);
      } finally {
        setLoading(false);
      }
    };

    loadClubs();
  }, [token]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">All Clubs</h2>
      {clubs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No clubs available at the moment.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clubs.map((club) => (
            <ClubCard key={club.id} club={club} token={token} />
          ))}
        </div>
      )}
    </div>
  );
}