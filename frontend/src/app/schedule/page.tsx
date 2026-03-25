// Train Search and Booking Page
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface Train {
  _id: string;
  number: string;
  name: string;
  from: string;
  to: string;
  departureTime: string;
  arrivalTime: string;
  duration: string;
  classes: string[];
  price: { [key: string]: number };
  availability: { confirmed: number; rac: number; waitlist: number };
  amenities: string[];
  rating: number;
  reviews: number;
}

export default function TrainSearchPage() {
  const [fromStation, setFromStation] = useState("");
  const [toStation, setToStation] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  const [seatClass, setSeatClass] = useState("AC2");
  const [trains, setTrains] = useState<Train[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [sortBy, setSortBy] = useState("departure_time");
  const [pageSize, setPageSize] = useState(10);

  const indianCities = [
    "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Chandigarh", "Indore", "Bhopal", "Visakhapatnam", "Kochi"
  ];

  const handleSearch = async (e: React.FormEvent, page: number = 1) => {
    e?.preventDefault();
    setLoading(true);
    setError("");
    setCurrentPage(page);

    try {
      const response = await fetch(
        `http://localhost:10000/api/trains/search?from_station=${fromStation}&to_station=${toStation}&departure_date=${departureDate}&seat_class=${seatClass}&page=${page}&limit=${pageSize}&sort_by=${sortBy}`
      );

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = Array.isArray(data.detail) 
          ? data.detail.map((e: any) => e.msg).join("; ")
          : data.detail;
        setError(errorMsg || "Error searching trains");
        return;
      }

      setTrains(data.trains || []);
      setTotalPages(data.total_pages || 1);
      setTotalResults(data.total_results || 0);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const swapStations = () => {
    const currentFrom = fromStation;
    setFromStation(toStation);
    setToStation(currentFrom);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div className="text-3xl font-bold flex items-center gap-2">
              🚂 TATKAL Train Booking
            </div>
            <Link href="/profile" className="hover:bg-white/20 px-4 py-2 rounded-lg transition">
              👤 Profile
            </Link>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
              {/* From Station */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📍 From
                </label>
                <select
                  value={fromStation}
                  onChange={(e) => setFromStation(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  {indianCities.map((city) => (
                    <option key={city} value={city}>
                      {city}
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap Button */}
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={swapStations}
                  className="w-full h-10 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition font-semibold flex items-center justify-center gap-2"
                >
                  🔄 Swap
                </button>
              </div>

              {/* To Station */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📍 To
                </label>
                <select
                  value={toStation}
                  onChange={(e) => setToStation(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select</option>
                  {indianCities.map((city) => (
                    <option key={city} value={city}>
                      {city}
                    </option>
                  ))}
                </select>
              </div>

              {/* Departure Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📅 Date
                </label>
                <input
                  type="date"
                  value={departureDate}
                  onChange={(e) => setDepartureDate(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Seat Class */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  💺 Class
                </label>
                <select
                  value={seatClass}
                  onChange={(e) => setSeatClass(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="General">General</option>
                  <option value="Sleeper">Sleeper</option>
                  <option value="AC3">AC3</option>
                  <option value="AC2">AC2</option>
                  <option value="AC1">AC1</option>
                </select>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-2.5 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition disabled:opacity-50"
              >
                {loading ? "Searching..." : "🔍 Search Trains"}
              </button>
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className="px-6 bg-gray-200 hover:bg-gray-300 rounded-lg transition font-semibold"
              >
                ⚙️ Filters
              </button>
            </div>

            {/* Sorting & Filter Options */}
            {showFilters && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📊 Sort By
                    </label>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="departure_time">Departure Time</option>
                      <option value="price">Price (Low to High)</option>
                      <option value="duration">Duration</option>
                      <option value="rating">Rating (High to Low)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📄 Results Per Page
                    </label>
                    <select
                      value={pageSize}
                      onChange={(e) => setPageSize(parseInt(e.target.value))}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="5">5 Trains</option>
                      <option value="10">10 Trains</option>
                      <option value="20">20 Trains</option>
                      <option value="50">50 Trains</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      type="button"
                      onClick={(e) => handleSearch(e as any, 1)}
                      disabled={loading}
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 rounded-lg transition disabled:opacity-50"
                    >
                      Apply Filters
                    </button>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mt-6">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        </div>
      )}

      {/* Train Results */}
      <div className="max-w-7xl mx-auto mt-8 px-4 pb-12">
        {trains.length > 0 ? (
          <>
            {/* Results Summary */}
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-gray-700">
                Showing <strong>{trains.length}</strong> of <strong>{totalResults}</strong> trains available • 
                Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
              </p>
            </div>

            {/* Train Cards Grid */}
            <div className="grid gap-4">
              {trains.map((train) => (
                <div key={train._id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Train Info */}
                    <div>
                      <div className="text-lg font-bold text-gray-800">{train.name}</div>
                      <div className="text-sm text-gray-600">#{train.number}</div>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-yellow-500">⭐</span>
                        <span className="text-sm font-semibold">{train.rating}</span>
                        <span className="text-xs text-gray-500">({train.reviews} reviews)</span>
                      </div>
                    </div>

                    {/* Timing */}
                    <div>
                      <div className="text-2xl font-bold text-gray-800">{train.departureTime}</div>
                      <div className="text-xs text-gray-600">Departure</div>
                      <div className="mt-4 text-2xl font-bold text-gray-800">{train.arrivalTime}</div>
                      <div className="text-xs text-gray-600">Arrival</div>
                      <div className="mt-2 text-sm text-blue-600 font-semibold">{train.duration}</div>
                    </div>

                    {/* Route */}
                    <div>
                      <div className="text-sm text-gray-600">Route</div>
                      <div className="font-bold text-gray-800">{train.from}</div>
                      <div className="text-center text-gray-400 py-2">↓</div>
                      <div className="font-bold text-gray-800">{train.to}</div>
                    </div>

                    {/* Availability & Price */}
                    <div>
                      <div className="text-sm text-gray-600 mb-2">Seats Available</div>
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between text-xs">
                          <span>✓ Confirmed</span>
                          <span className="font-bold text-green-600">{train.availability.confirmed}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span>◐ RAC</span>
                          <span className="font-bold text-yellow-600">{train.availability.rac}</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span>✗ Waitlist</span>
                          <span className="font-bold text-red-600">{train.availability.waitlist}</span>
                        </div>
                      </div>

                      {/* Price & Book Button */}
                      <div className="border-t pt-3">
                        <div className="text-xs text-gray-600">Price per seat</div>
                        <div className="text-2xl font-bold text-gray-800">
                          ₹{train.price[seatClass] || train.price["AC2"]}
                        </div>
                        <Link
                          href={`/booking/${train._id}`}
                          className="w-full mt-3 block text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-2 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition"
                        >
                          Book Now
                        </Link>
                      </div>
                    </div>
                  </div>

                  {/* Amenities */}
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-xs text-gray-600 mb-2">Amenities</div>
                    <div className="flex flex-wrap gap-2">
                      {train.amenities.map((amenity) => (
                        <span key={amenity} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                          {amenity}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2 flex-wrap">
                <button
                  disabled={currentPage === 1 || loading}
                  onClick={(e) => handleSearch(e as any, currentPage - 1)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  ← Previous
                </button>

                {/* Page Numbers */}
                <div className="flex gap-1">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    const page = currentPage > 3 ? currentPage - 2 + i : i + 1;
                    if (page > totalPages) return null;
                    return (
                      <button
                        key={page}
                        onClick={(e) => handleSearch(e as any, page)}
                        disabled={loading}
                        className={`px-3 py-2 rounded-lg transition ${
                          currentPage === page
                            ? "bg-indigo-600 text-white font-semibold"
                            : "bg-gray-200 hover:bg-gray-300"
                        } disabled:opacity-50`}
                      >
                        {page}
                      </button>
                    );
                  })}
                  {totalPages > 5 && <span className="text-gray-600">...</span>}
                </div>

                <button
                  disabled={currentPage === totalPages || loading}
                  onClick={(e) => handleSearch(e as any, currentPage + 1)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🚂</div>
            <p className="text-gray-600 text-lg">
              {loading ? "Searching for trains..." : "Select route and date to search for trains"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
