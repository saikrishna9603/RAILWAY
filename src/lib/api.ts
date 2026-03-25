/**
 * API Configuration and Utility Functions
 * All API calls should go through this file for proper URL handling
 */

// Use backend host from env if provided, otherwise point to the local development server.
const BACKEND_ENV_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const API_URL = BACKEND_ENV_URL ? BACKEND_ENV_URL.replace(/\/+$/, '') : 'http://localhost:10000';

export function getApiUrl(endpoint: string): string {
  // Remove leading slash from endpoint if present
  const path = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_URL}/${path}`;
}

export async function apiCall<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: Record<string, any>,
  headers?: Record<string, string>,
  callOptions?: { silent?: boolean }
): Promise<T> {
  const url = getApiUrl(endpoint);
  
  // Get auth token if available
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  
  const requestOptions: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...headers,
    },
  };

  if (body && (method === 'POST' || method === 'PUT')) {
    requestOptions.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, requestOptions);
    
    if (!response.ok) {
      const errorText = await response.text();

      // Treat no-train routes as a valid empty search result, not an app error.
      if (endpoint.includes('api/trains/search') && response.status === 404) {
        return {
          trains: [],
          total_results: 0,
          total_pages: 1,
          showing_results: 0,
        } as any;
      }
      
      throw new Error(`API Error (${response.status}): ${errorText}`);
    }

    return response.json();
  } catch (error: any) {
    if (!callOptions?.silent) {
      console.error('API Call Error:', error);
    }

    throw error;
  }
}

// Specific API methods for common endpoints
export const API = {
  // Auth
  login: async (email: string, password: string) => {
    const response = await fetch(getApiUrl('api/auth/login'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    if (!response.ok) {
      const message =
        typeof data?.detail === 'string'
          ? data.detail
          : `Login failed (${response.status})`;
      throw new Error(message);
    }

    return data;
  },
  register: (email: string, password: string, name: string) =>
    apiCall('api/auth/register', 'POST', { email, password, name }),

  // Trains
  searchTrains: (from: string, to: string, date: string, seatClass: string, page: number = 1, limit: number = 10, sortBy: string = 'price') =>
    apiCall(`api/trains/search?from_station=${from}&to_station=${to}&departure_date=${date}&seat_class=${seatClass}&page=${page}&limit=${limit}&sort_by=${sortBy}`),
  getTrainDetail: (trainId: string | number) =>
    apiCall(`api/trains/${trainId}`),
  getTrainSeatMap: (trainId: string | number) =>
    apiCall(`api/trains/${trainId}/seat-map`),

  // Bookings
  executeBooking: async (bookingData: Record<string, any>) => {
    try {
      return await apiCall('api/bookings/execute', 'POST', bookingData);
    } catch (error: any) {
      // Some environments expose normal booking route while execute can intermittently 404.
      if (typeof error?.message === 'string' && error.message.includes('API Error (404)')) {
        return apiCall('api/bookings/normal', 'POST', bookingData);
      }
      throw error;
    }
  },
  getBookingHistory: (userId: string) =>
    apiCall(`api/bookings/history/${userId}`),
  cancelBooking: (bookingId: string, reason: string, pnr: string = '') => {
    const userId = typeof window !== 'undefined'
      ? (JSON.parse(localStorage.getItem('user') || '{}')?.user_id || 'demo_user_001')
      : 'demo_user_001';

    return apiCall(`api/bookings/${bookingId}/cancel`, 'POST', {
      booking_id: bookingId,
      pnr,
      reason,
      user_id: userId,
    });
  },
  createBooking: async (bookingData: Record<string, any>) => {
    try {
      return await apiCall('api/booking/create', 'POST', bookingData, undefined, { silent: true });
    } catch {
      const passengerCount = Array.isArray(bookingData?.passengers)
        ? bookingData.passengers.length
        : Number(bookingData?.passengers || 1);

      const executePayload = {
        user_id: bookingData?.user_id || bookingData?.userId || 'demo_user_001',
        train_id: bookingData?.train_id || bookingData?.trainId,
        passengers: passengerCount,
        class: bookingData?.seat_class || bookingData?.class || '2A',
        seat_preference: bookingData?.seat_preference || bookingData?.seatPreference || 'any',
      };

      let executeResult: any;
      try {
        executeResult = await apiCall('api/bookings/execute', 'POST', executePayload, undefined, { silent: true });
      } catch {
        executeResult = await apiCall('api/bookings/normal', 'POST', executePayload, undefined, { silent: true });
      }

      return {
        success: true,
        booking_id: executeResult?.booking_id,
        pnr: executeResult?.pnr,
        train_name: bookingData?.train_name || bookingData?.trainName,
        train_number: bookingData?.train_number || bookingData?.trainNumber,
        from_station: bookingData?.from_station || bookingData?.from,
        to_station: bookingData?.to_station || bookingData?.to,
        departure_date: bookingData?.departure_date || bookingData?.date,
        departure_time: bookingData?.departure_time || bookingData?.departureTime,
        arrival_time: bookingData?.arrival_time || bookingData?.arrivalTime,
        seat_class: bookingData?.seat_class || bookingData?.class,
        passengers: bookingData?.passengers || [],
        total_amount: bookingData?.total_amount || bookingData?.totalAmount || 0,
        status: executeResult?.status || 'CONFIRMED',
        booking_type: bookingData?.booking_type || bookingData?.bookingType || 'normal',
        created_at: new Date().toISOString(),
      };
    }
  },

  // Tatkal
  scheduleTatkal: (data: Record<string, any>) =>
    apiCall('api/bookings/tatkal', 'POST', data),
  getTatkalStatus: (tatkalBookingId: string) =>
    apiCall(`api/bookings/tatkal/${tatkalBookingId}/status`),

  // Profile
  getProfile: (userId: string) =>
    apiCall(`api/profile/${userId}`),
  updateProfile: (userId: string, data: Record<string, any>) =>
    apiCall('api/profile/update', 'POST', { user_id: userId, ...data }),

  // Agents
  orchestrateBooking: (data: Record<string, any>) => {
    const params = data?.parameters || data || {};
    const query = new URLSearchParams({
      user_id: data?.user_id || 'demo_user_001',
      train_id: data?.train_id || params?.train_id || 'train_0001',
      from_station: params?.from_station || params?.from || 'Delhi',
      to_station: params?.to_station || params?.to || 'Mumbai',
      departure_date: params?.departure_date || params?.date || new Date().toISOString().split('T')[0],
    });
    return apiCall(`api/agents/orchestrate?${query.toString()}`, 'POST', {});
  },
  getAgentLogs: (orchestrationId: string) =>
    apiCall(`api/agents/logs/${orchestrationId}`),
  getAgentHealth: () =>
    apiCall('api/agents/health'),

  // System
  getSystemStats: () =>
    apiCall('api/system/stats'),
  getDashboardStats: () =>
    apiCall('api/dashboard/stats'),
};

export default API;
