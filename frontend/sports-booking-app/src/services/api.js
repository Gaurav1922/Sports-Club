const API_BASE_URL = 'http://localhost:8000/api';

const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Token ${token}` }),
    },
    ...options,
  };

  if (config.body) {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(url, config);
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  
  return response.json();
};

export const api = {
  sendOTP: (phoneNumber) => 
    apiCall('/auth/send-otp/', {
      method: 'POST',
      body: { phone_number: phoneNumber }
    }),
  
  verifyOTP: (phoneNumber, otp) => 
    apiCall('/auth/verify-otp/', {
      method: 'POST',
      body: { phone_number: phoneNumber, otp }
    }),
  
  getNearbyCubs: (lat, lng, radius = 10) => 
    apiCall(`/clubs/nearby/?lat=${lat}&lng=${lng}&radius=${radius}`),
  
  getAvailableSlots: (clubId, date) => 
    apiCall(`/clubs/${clubId}/available_slots/?date=${date}`),
  
  createBooking: (bookingData) => 
    apiCall('/bookings/', {
      method: 'POST',
      body: bookingData
    }),
  
  getUserBookings: () => 
    apiCall('/bookings/history/'),
};