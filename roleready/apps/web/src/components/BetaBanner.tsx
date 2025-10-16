"use client";

import { useState } from "react";

export default function BetaBanner() {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="bg-gradient-to-r from-green-500 to-blue-600 text-white py-3 px-4 relative">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="bg-white text-green-600 px-2 py-1 rounded-full text-xs font-bold">
            BETA
          </span>
          <div>
            <p className="font-semibold">🟢 RoleReady Public Beta</p>
            <p className="text-sm opacity-90">
              Free access to all premium features during beta phase
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="hidden md:block text-sm">
            <span className="opacity-90">All features unlocked • No limits • </span>
            <span className="font-semibold">Free for early users</span>
          </div>
          <button
            onClick={() => setIsVisible(false)}
            className="text-white hover:text-gray-200 transition-colors"
            aria-label="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
