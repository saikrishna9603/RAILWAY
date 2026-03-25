'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import API from '@/lib/api';
import { calculateFareBreakdown } from '@/lib/pricing';

type Passenger = {
  name: string;
  age: string;
};

type TrainDetails = {
  trainName: string;
  trainNumber: string;
  from: string;
  to: string;
  departureTime: string;
  arrivalTime: string;
  price: number;
  availableSeats: number;
  date: string;
  bookingType: 'normal' | 'tatkal';
};

export default function BookingPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const trainId = params.id;
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [trainDetails, setTrainDetails] = useState<TrainDetails>({
    trainName: '',
    trainNumber: '',
    from: '',
    to: '',
    departureTime: '',
    arrivalTime: '',
    price: 2500,
    availableSeats: 0,
    date: '',
    bookingType: 'normal',
  });
  const [formData, setFormData] = useState({
    passengers: 1,
    class: '2A',
    seat_preference: 'any',
  });
  const [passengers, setPassengers] = useState<Passenger[]>([{ name: '', age: '' }]);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    setUser(JSON.parse(userData));
  }, [router]);

  useEffect(() => {
    const trainName = searchParams.get('trainName') || '';
    const trainNumber = searchParams.get('trainNumber') || '';
    const from = searchParams.get('from') || '';
    const to = searchParams.get('to') || '';
    const departureTime = searchParams.get('departureTime') || '';
    const arrivalTime = searchParams.get('arrivalTime') || '';
    const price = Number(searchParams.get('price') || 2500);
    const availableSeats = Number(searchParams.get('availableSeats') || 0);
    const date = searchParams.get('date') || '';
    const bookingType = (searchParams.get('bookingType') as 'normal' | 'tatkal') || 'normal';

    console.log('🎫 Booking Page - Search Params loaded:', { trainName, trainNumber, from, to, date, bookingType });

    if (trainName && trainNumber) {
      setTrainDetails({
        trainName,
        trainNumber,
        from,
        to,
        departureTime,
        arrivalTime,
        price: Number.isFinite(price) ? price : 2500,
        availableSeats: Number.isFinite(availableSeats) ? availableSeats : 0,
        date,
        bookingType,
      });
      return;
    }

    const fetchTrainDetails = async () => {
      try {
        const train = await API.getTrainDetail(String(trainId)) as any;
        setTrainDetails((prev) => ({
          ...prev,
          trainName: train?.name || 'Selected Train',
          trainNumber: train?.number || String(trainId),
          from: train?.from || '',
          to: train?.to || '',
          departureTime: train?.departureTime || '',
          arrivalTime: train?.arrivalTime || '',
          price: Number(train?.price?.[formData.class] || train?.price?.AC2 || 2500),
          availableSeats: Number(train?.availability?.confirmed || 0),
        }));
      } catch {
        setTrainDetails((prev) => ({
          ...prev,
          trainName: 'Selected Train',
          trainNumber: String(trainId),
        }));
      }
    };

    fetchTrainDetails();
  }, [searchParams, trainId, formData.class]);

  useEffect(() => {
    setPassengers((prev) => {
      if (prev.length === formData.passengers) return prev;
      if (prev.length > formData.passengers) return prev.slice(0, formData.passengers);

      const next = [...prev];
      while (next.length < formData.passengers) {
        next.push({ name: '', age: '' });
      }
      return next;
    });
  }, [formData.passengers]);

  // Calculate pricing using dynamic pricing engine
  // IMPORTANT: Must be BEFORE early return to respect Rules of Hooks
  const priceBreakdown = useMemo(() => {
    if (!trainDetails.from || !trainDetails.to) {
      console.log('⚠️ Price breakdown skipped - from/to missing:', { from: trainDetails.from, to: trainDetails.to });
      return {
        base: 0,
        gst: 0,
        fee: 50,
        tatkalCharge: 0,
        total: 0,
      };
    }

    const fareData = calculateFareBreakdown({
      from: trainDetails.from,
      to: trainDetails.to,
      travelClass: formData.class,
      bookingMode: trainDetails.bookingType || 'normal',
      passengerCount: formData.passengers,
    });

    console.log('✅ Price breakdown calculated:', {
      from: trainDetails.from,
      to: trainDetails.to,
      class: formData.class,
      passengers: formData.passengers,
      bookingType: trainDetails.bookingType,
      result: fareData,
    });

    return {
      base: fareData.total.baseFare,
      gst: fareData.total.gst,
      fee: fareData.total.bookingFee,
      tatkalCharge: fareData.total.tatkalCharge,
      total: fareData.total.grandTotal,
    };
  }, [trainDetails.from, trainDetails.to, formData.class, formData.passengers, trainDetails.bookingType]);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    if (loading) return;

    const hasInvalidPassenger = passengers.some(
      (p) => !p.name.trim() || !Number.isFinite(Number(p.age)) || Number(p.age) <= 0
    );
    if (hasInvalidPassenger) {
      setMessage('❌ Please fill valid passenger details before continuing to payment.');
      return;
    }

    setLoading(true);
    try {
      const bookingDraft = {
        trainId: String(trainId),
        trainName: trainDetails.trainName,
        trainNumber: trainDetails.trainNumber,
        from: trainDetails.from,
        to: trainDetails.to,
        departureTime: trainDetails.departureTime,
        arrivalTime: trainDetails.arrivalTime,
        date: trainDetails.date || new Date().toISOString().split('T')[0],
        class: formData.class,
        seatPreference: formData.seat_preference,
        passengers: passengers.map((p) => ({ name: p.name.trim(), age: Number(p.age) })),
        price: priceBreakdown.total, // Use dynamic pricing
        bookingType: trainDetails.bookingType || 'normal',
        availableSeats: trainDetails.availableSeats,
        train_id: trainId,
        userId: user?.user_id || 'demo_user_001',
      };

      sessionStorage.setItem('bookingDraft', JSON.stringify(bookingDraft));
      router.push('/payment');
    } catch (error: any) {
      setMessage('❌ Error: ' + (error.message || 'Booking failed'));
    } finally {
      setLoading(false);
    }
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-3xl font-bold">🎫 Book Your Ticket</h1>
          <Link
            href="/schedule"
            className="bg-white text-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg font-semibold transition"
          >
            ← Back
          </Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Booking Form */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Booking Details</h2>

            <div className="mb-6 p-4 border border-blue-200 bg-blue-50 rounded-lg">
              <p className="font-bold text-gray-800">{trainDetails.trainName || 'Selected Train'} ({trainDetails.trainNumber || trainId})</p>
              <p className="text-sm text-gray-700 mt-1">
                {trainDetails.from || 'N/A'} ({trainDetails.departureTime || '--:--'}) → {trainDetails.to || 'N/A'} ({trainDetails.arrivalTime || '--:--'})
              </p>
              <p className="text-sm text-gray-600 mt-1">Available Seats: {trainDetails.availableSeats}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-2">
                  Number of Passengers
                </label>
                <input
                  type="number"
                  min="1"
                  max="6"
                  value={formData.passengers}
                  onChange={(e) => {
                    const parsed = Number(e.target.value);
                    const safePassengers = Number.isFinite(parsed) && parsed > 0
                      ? Math.min(parsed, 6)
                      : 1;
                    setFormData({ ...formData, passengers: safePassengers });
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-2">
                  Coach Class
                </label>
                <select
                  value={formData.class}
                  onChange={(e) => setFormData({ ...formData, class: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="1A">1A (First AC)</option>
                  <option value="2A">2A (AC 2-Tier)</option>
                  <option value="3A">3A (AC 3-Tier)</option>
                  <option value="SL">SL (Sleeper)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-600 mb-2">
                  Seat Preference
                </label>
                <select
                  value={formData.seat_preference}
                  onChange={(e) => setFormData({ ...formData, seat_preference: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="any">Any Available</option>
                  <option value="window">Window</option>
                  <option value="middle">Middle</option>
                  <option value="aisle">Aisle</option>
                </select>
              </div>

              <div className="border-t pt-6">
                <h3 className="font-bold text-gray-800 mb-4">Passenger Details</h3>
                <div className="space-y-4">
                  {Array.from({ length: formData.passengers }).map((_, i) => (
                    <div key={i} className="p-4 border border-gray-200 rounded-lg">
                      <p className="font-semibold text-gray-800">Passenger {i + 1}</p>
                      <input
                        type="text"
                        placeholder="Full name"
                        value={passengers[i]?.name || ''}
                        onChange={(e) => {
                          const value = e.target.value;
                          setPassengers((prev) => prev.map((p, idx) => (idx === i ? { ...p, name: value } : p)));
                        }}
                        className="w-full mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <input
                        type="number"
                        min="1"
                        placeholder="Age"
                        value={passengers[i]?.age || ''}
                        onChange={(e) => {
                          const value = e.target.value;
                          setPassengers((prev) => prev.map((p, idx) => (idx === i ? { ...p, age: value } : p)));
                        }}
                        className="w-full mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {message && (
                <div className={`p-4 rounded-lg font-semibold ${
                  message.includes('✅') 
                    ? 'bg-green-100 text-green-900'
                    : 'bg-red-100 text-red-900'
                }`}>
                  {message}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-3 rounded-lg font-bold transition text-lg"
              >
                {loading ? 'Preparing Payment...' : 'Continue to Payment'}
              </button>
            </form>
          </div>

          {/* Price Summary */}
          <div className="bg-white rounded-lg shadow-lg p-6 h-fit sticky top-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">💰 Price Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Base Fare ({formData.passengers} × {formData.class})</span>
                <span className="font-semibold">₹{priceBreakdown.base.toLocaleString('en-IN')}</span>
              </div>
              {priceBreakdown.tatkalCharge > 0 && (
                <div className="flex justify-between text-sm">
                  <span>Tatkal Charge</span>
                  <span className="font-semibold">₹{priceBreakdown.tatkalCharge.toLocaleString('en-IN')}</span>
                </div>
              )}
              {priceBreakdown.gst > 0 && (
                <div className="flex justify-between text-sm">
                  <span>GST (5%)</span>
                  <span className="font-semibold">₹{priceBreakdown.gst.toLocaleString('en-IN')}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span>Booking Fee</span>
                <span className="font-semibold">₹{priceBreakdown.fee.toLocaleString('en-IN')}</span>
              </div>
              <div className="border-t pt-3 flex justify-between">
                <span className="font-bold">Total Amount</span>
                <span className="font-bold text-lg text-green-600">
                  ₹{priceBreakdown.total.toLocaleString('en-IN')}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-3 italic">Pricing calculated based on IRCTC-style dynamic rate system</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
