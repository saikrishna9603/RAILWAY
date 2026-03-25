// Tatkal Booking System Page
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

export default function TatkalBookingPage() {
  const [selectedTrain, setSelectedTrain] = useState<string>("");
  const [scheduledTime, setScheduledTime] = useState<string>("");
  const [passengers, setPassengers] = useState<number>(1);
  const [seatClass, setSeatClass] = useState<string>("AC2");
  const [isScheduled, setIsScheduled] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [tatkalId, setTatkalId] = useState<string>("");
  const [countdownTime, setCountdownTime] = useState<string>("");

  useEffect(() => {
    if (!isScheduled) return;

    const interval = setInterval(() => {
      const now = new Date();
      const [hours, minutes] = scheduledTime.split(":").map(Number);
      const scheduledDate = new Date();
      scheduledDate.setHours(hours, minutes, 0);

      const diff = scheduledDate.getTime() - now.getTime();

      if (diff > 0) {
        const h = Math.floor(diff / (1000 * 60 * 60));
        const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const s = Math.floor((diff % (1000 * 60)) / 1000);
        setCountdownTime(`${h}h ${m}m ${s}s`);
      } else {
        setCountdownTime("Tatkal booking started!");
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isScheduled, scheduledTime]);

  const handleScheduleTatkal = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://localhost:10000/api/bookings/tatkal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: localStorage.getItem("user") || "",
          train_id: selectedTrain,
          train_number: selectedTrain,
          from_station: "Delhi",
          to_station: "Mumbai",
          departure_date: new Date().toISOString().split("T")[0],
          passengers: Array(passengers).fill({
            name: "Passenger",
            age: 25,
            gender: "M",
            document_type: "Aadhaar",
            document_number: "123456789012",
            phone: "9876543210",
          }),
          seat_class: seatClass,
          payment: {
            payment_method: "CREDIT_CARD",
            amount: 1000 * passengers,
          },
          mobile_number: "9876543210",
          email: "user@example.com",
          scheduled_time: scheduledTime,
          retry_count: 5,
          retry_interval: 2,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        alert("Error: " + (data.detail || "Failed to schedule Tatkal booking"));
        return;
      }

      setTatkalId(data.tatkal_booking_id);
      setIsScheduled(true);
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-orange-100 to-red-100">
      {/* Animated Header */}
      <div className="bg-gradient-to-r from-orange-500 via-red-500 to-red-600 text-white p-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="animate-pulse text-6xl">⚡</div>
        </div>
        <div className="relative max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">⚡ TATKAL Booking System</h1>
          <p className="text-orange-100 text-lg">Book trains instantly at lightning speed!</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2">
            {!isScheduled ? (
              <div className="bg-white rounded-lg shadow-2xl p-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Schedule Your Tatkal Booking</h2>

                <form onSubmit={handleScheduleTatkal} className="space-y-6">
                  {/* Train Selection */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      🚂 Select Train
                    </label>
                    <select
                      value={selectedTrain}
                      onChange={(e) => setSelectedTrain(e.target.value)}
                      required
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      <option value="">Choose a train...</option>
                      <option value="train_001">12345 - Rajdhani Express</option>
                      <option value="train_002">22222 - Shatabdi Express</option>
                      <option value="train_003">33333 - Duronto Express</option>
                    </select>
                  </div>

                  {/* Scheduled Time */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      ⏰ Schedule Booking Time
                    </label>
                    <input
                      type="time"
                      value={scheduledTime}
                      onChange={(e) => setScheduledTime(e.target.value)}
                      required
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Tatkal booking opens at 10:00 AM daily. Schedule your booking just before this time.
                    </p>
                  </div>

                  {/* Passengers */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      👥 Number of Passengers
                    </label>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5, 6].map((num) => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => setPassengers(num)}
                          className={`px-4 py-2 rounded-lg font-semibold transition ${
                            passengers === num
                              ? "bg-orange-500 text-white"
                              : "bg-gray-200 text-gray-800 hover:bg-gray-300"
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Seat Class */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      💺 Preferred Seat Class
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: "General", label: "General" },
                        { value: "Sleeper", label: "Sleeper" },
                        { value: "AC3", label: "AC 3-Tier" },
                        { value: "AC2", label: "AC 2-Tier" },
                      ].map((cls) => (
                        <button
                          key={cls.value}
                          type="button"
                          onClick={() => setSeatClass(cls.value)}
                          className={`p-3 rounded-lg font-semibold transition border-2 ${
                            seatClass === cls.value
                              ? "border-orange-500 bg-orange-50 text-orange-700"
                              : "border-gray-200 bg-gray-50 text-gray-700 hover:border-orange-300"
                          }`}
                        >
                          {cls.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Info Box */}
                  <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
                    <p className="text-sm text-orange-800 font-semibold mb-2">💡 Tips for Success:</p>
                    <ul className="text-xs text-orange-700 space-y-1 list-disc list-inside">
                      <li>Schedule booking 30 seconds before Tatkal opens (10:00 AM)</li>
                      <li>Ensure strong internet connection</li>
                      <li>Have all passenger details ready</li>
                      <li>Keep payment method verified</li>
                      <li>Max 6 passengers per booking</li>
                    </ul>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-600 text-white font-bold py-3 rounded-lg hover:from-orange-600 hover:to-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                  >
                    {loading ? "Scheduling..." : "⚡ Schedule Tatkal Booking"}
                  </button>
                </form>
              </div>
            ) : (
              /* Tatkal Tracking */
              <div className="bg-white rounded-lg shadow-2xl p-8 text-center">
                <div className="text-6xl mb-4 animate-bounce">⚡</div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Tatkal Booking Scheduled!</h2>
                <p className="text-gray-600 mb-6">Your booking will execute at the scheduled time</p>

                <div className="bg-gradient-to-r from-orange-100 to-red-100 rounded-lg p-6 mb-6">
                  <p className="text-sm text-gray-600 mb-2">Booking ID</p>
                  <p className="text-2xl font-bold text-orange-600 font-mono">{tatkalId}</p>
                </div>

                {/* Countdown */}
                <div className="bg-blue-50 rounded-lg p-6 mb-6">
                  <p className="text-sm text-gray-600 mb-2">Time Remaining</p>
                  <p className="text-4xl font-bold text-blue-600 font-mono">{countdownTime}</p>
                </div>

                {/* Status Info */}
                <div className="space-y-3 text-left mb-6">
                  <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                    <span className="text-2xl">✅</span>
                    <div>
                      <p className="font-semibold text-gray-800">Booking Scheduled</p>
                      <p className="text-sm text-gray-600">Ready to execute</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                    <span className="text-2xl">⏳</span>
                    <div>
                      <p className="font-semibold text-gray-800">Waiting for Time</p>
                      <p className="text-sm text-gray-600">Will verify availability at scheduled time</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                    <span className="text-2xl">🚀</span>
                    <div>
                      <p className="font-semibold text-gray-800">Auto Retry Active</p>
                      <p className="text-sm text-gray-600">Max 5 retry attempts</p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setIsScheduled(false);
                    setTatkalId("");
                    setCountdownTime("");
                  }}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
                >
                  Schedule Another Booking
                </button>
              </div>
            )}
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            {/* Feature Card 1 */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-3">⚡ What is Tatkal?</h3>
              <p className="text-sm text-gray-600">
                Tatkal booking opens at 10:00 AM for next-day travel and 11:00 AM for same-day
                travel. Our AI system helps you book instantly!
              </p>
            </div>

            {/* Feature Card 2 */}
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-lg shadow-lg p-6 text-white">
              <h3 className="text-lg font-bold mb-3">🎯 Success Rate</h3>
              <p className="text-sm text-orange-100 mb-4">
                Our PRAL agents have 87% success rate in booking confirmed seats within 2 seconds
              </p>
              <div className="bg-white/20 rounded-lg p-3">
                <div className="flex items-center justify-between text-sm font-semibold mb-2">
                  <span>Your Success Probability</span>
                  <span>87%</span>
                </div>
                <div className="w-full h-2 bg-white/30 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-white rounded-full"
                    style={{ width: "87%" }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Feature Card 3 */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-3">📊 Latest Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Bookings Today</span>
                  <span className="font-bold text-lg">1,247</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Success Rate</span>
                  <span className="font-bold text-lg text-green-600">94%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Avg Booking Time</span>
                  <span className="font-bold text-lg">1.2 sec</span>
                </div>
              </div>
            </div>

            {/* Back Button */}
            <Link
              href="/"
              className="w-full block text-center bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 rounded-lg transition"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
