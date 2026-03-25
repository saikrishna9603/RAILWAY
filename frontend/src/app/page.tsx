// Dashboard Page Component
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface BookingStats {
  total_bookings: number;
  successful_bookings: number;
  cancelled_bookings: number;
  total_money_spent: number;
}

interface UserData {
  user_id: string;
  email: string;
  full_name: string;
  phone: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [stats, setStats] = useState<BookingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [recentBookings, setRecentBookings] = useState([]);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (!userData) {
      // Auto-login with demo user for demo mode
      const demoUser = {
        user_id: 'demo_user_001',
        email: 'user@example.com',
        full_name: 'John Doe',
        phone: '+919876543210'
      };
      localStorage.setItem("user", JSON.stringify(demoUser));
      localStorage.setItem("access_token", "demo_token_12345");
      setUser(demoUser);
      setStats({
        total_bookings: 0,
        successful_bookings: 0,
        cancelled_bookings: 0,
        total_money_spent: 0,
      });
      setLoading(false);
      return;
    }

    const parsedUser = JSON.parse(userData);
    setUser(parsedUser);
    fetchDashboardData(parsedUser.user_id);
  }, []);

  const fetchDashboardData = async (userId: string) => {
    try {
      // Fetch profile
      const profileResponse = await fetch(`http://localhost:10000/api/profile/${userId}`);
      if (profileResponse.ok) {
        const profileData = await profileResponse.json();
        setStats({
          total_bookings: profileData.total_bookings || 0,
          successful_bookings: profileData.successful_bookings || 0,
          cancelled_bookings: 0,
          total_money_spent: 0,
        });
      }

      // Fetch booking history
      const bookingsResponse = await fetch(
        `http://localhost:10000/api/bookings/history/${userId}`
      );
      if (bookingsResponse.ok) {
        const bookingsData = await bookingsResponse.json();
        setRecentBookings(bookingsData.bookings?.slice(0, 5) || []);
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🚂</div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome, {user?.full_name}! 👋</h1>
            <p className="text-blue-100 mt-1">{user?.email}</p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/schedule"
              className="bg-white text-blue-600 hover:bg-blue-50 px-4 py-2 rounded-lg font-semibold transition"
            >
              Book New Train
            </Link>
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg font-semibold transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="text-4xl mb-2">🎫</div>
            <p className="text-gray-600 text-sm">Total Bookings</p>
            <p className="text-3xl font-bold text-blue-600">
              {stats?.total_bookings || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-gray-600 text-sm">Successful</p>
            <p className="text-3xl font-bold text-green-600">
              {stats?.successful_bookings || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="text-4xl mb-2">💰</div>
            <p className="text-gray-600 text-sm">Total Spent</p>
            <p className="text-3xl font-bold text-indigo-600">
              ₹{(stats?.total_money_spent || 0).toLocaleString()}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="text-4xl mb-2">🚀</div>
            <p className="text-gray-600 text-sm">Tatkal Success</p>
            <p className="text-3xl font-bold text-orange-600">
              {stats?.total_bookings ? Math.round((stats.successful_bookings / stats.total_bookings) * 100) : 0}%
            </p>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link
                  href="/schedule"
                  className="w-full block text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition font-semibold"
                >
                  🔍 Search Trains
                </Link>
                <Link
                  href="/booking/new"
                  className="w-full block text-center bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 rounded-lg hover:from-green-700 hover:to-emerald-700 transition font-semibold"
                >
                  📝 New Booking
                </Link>
                <Link
                  href="/payment"
                  className="w-full block text-center bg-gradient-to-r from-orange-600 to-red-600 text-white py-2 rounded-lg hover:from-orange-700 hover:to-red-700 transition font-semibold"
                >
                  💳 Manage Payments
                </Link>
              </div>
            </div>

            {/* Tatkal Booking */}
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
              <h3 className="text-lg font-bold mb-2">⚡ Tatkal Booking</h3>
              <p className="text-sm text-orange-100 mb-4">
                Get instant updates for Tatkal availability
              </p>
              <Link
                href="/booking/tatkal"
                className="w-full block text-center bg-white text-orange-600 py-2 rounded-lg hover:bg-orange-50 transition font-semibold"
              >
                Setup Tatkal Alert
              </Link>
            </div>
          </div>

          {/* Recent Bookings */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Recent Bookings</h3>
            {recentBookings.length > 0 ? (
              <div className="space-y-3">
                {recentBookings.map((booking: any) => (
                  <div
                    key={booking.booking_id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-bold text-gray-800">
                          {booking.train_number} - {booking.status}
                        </p>
                        <p className="text-sm text-gray-600">
                          PNR: {booking.pnr}
                        </p>
                        <p className="text-sm text-gray-600">
                          {booking.from_station} → {booking.to_station}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">₹{booking.total_fare || 0}</p>
                        <p className="text-xs text-gray-500">{booking.booking_date}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-600">
                <p>No bookings yet. 🚂</p>
                <Link href="/schedule" className="text-blue-600 hover:text-blue-700 font-semibold">
                  Book your first train
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/insights"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition text-center"
          >
            <div className="text-4xl mb-2">📊</div>
            <h3 className="font-bold text-gray-800">Insights</h3>
            <p className="text-sm text-gray-600 mt-1">View booking patterns</p>
          </Link>

          <Link
            href="/profile"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition text-center"
          >
            <div className="text-4xl mb-2">👤</div>
            <h3 className="font-bold text-gray-800">Profile</h3>
            <p className="text-sm text-gray-600 mt-1">Manage your account</p>
          </Link>

          <Link
            href="/ml-comparison"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition text-center"
          >
            <div className="text-4xl mb-2">🤖📊</div>
            <h3 className="font-bold text-gray-800">AI Comparison</h3>
            <p className="text-sm text-gray-600 mt-1">Agentic vs ML</p>
          </Link>

          <Link
            href="/live-agent"
            className="bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg shadow-lg p-6 hover:shadow-xl transition text-center text-white"
          >
            <div className="text-4xl mb-2">🤖</div>
            <h3 className="font-bold">AI Agent</h3>
            <p className="text-sm text-purple-100 mt-1">Get recommendations</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
