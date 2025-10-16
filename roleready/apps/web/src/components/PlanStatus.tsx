"use client";

import { useState, useEffect } from "react";

interface PlanInfo {
  plan_name: string;
  plan_display_name: string;
  status: string;
  is_beta: boolean;
  is_unlimited: boolean;
  billing_enabled: boolean;
  features: {
    [key: string]: {
      can_access: boolean;
      usage: {
        current: number;
        limit: number;
        unlimited: boolean;
      };
    };
  };
}

export default function PlanStatus() {
  const [planInfo, setPlanInfo] = useState<PlanInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlanInfo();
  }, []);

  const fetchPlanInfo = async () => {
    try {
      // Mock API call - in production this would call the real API
      const mockPlanInfo: PlanInfo = {
        plan_name: "beta_free",
        plan_display_name: "Public Beta — Free access (no limits)",
        status: "active",
        is_beta: true,
        is_unlimited: true,
        billing_enabled: false,
        features: {
          resume_parsing: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          resume_rewriting: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          job_matching: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          career_advisor: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          api_access: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          team_collaboration: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          multilingual: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          },
          export_formats: {
            can_access: true,
            usage: { current: 0, limit: -1, unlimited: true }
          }
        }
      };

      setPlanInfo(mockPlanInfo);
    } catch (error) {
      console.error('Error fetching plan info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!planInfo) {
    return null;
  }

  const getStatusColor = () => {
    if (planInfo.is_beta) return "text-green-600 bg-green-100";
    if (planInfo.is_unlimited) return "text-purple-600 bg-purple-100";
    return "text-blue-600 bg-blue-100";
  };

  const getStatusIcon = () => {
    if (planInfo.is_beta) return "🟢";
    if (planInfo.is_unlimited) return "⭐";
    return "📋";
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
            {getStatusIcon()} {planInfo.plan_display_name}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          Status: <span className="font-medium text-green-600">Active</span>
        </div>
      </div>

      {planInfo.is_beta && (
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-3 mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-green-600">🎉</span>
            <div>
              <p className="text-sm font-medium text-green-800">Public Beta Phase</p>
              <p className="text-xs text-green-600">
                Enjoy unlimited access to all features while we perfect the platform
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(planInfo.features).map(([feature, info]) => (
          <div key={feature} className="text-center">
            <div className={`w-3 h-3 rounded-full mx-auto mb-1 ${
              info.can_access ? 'bg-green-400' : 'bg-gray-300'
            }`}></div>
            <p className="text-xs text-gray-600 capitalize">
              {feature.replace('_', ' ')}
            </p>
            {info.usage.unlimited && (
              <p className="text-xs text-green-600 font-medium">Unlimited</p>
            )}
          </div>
        ))}
      </div>

      {planInfo.is_beta && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            💡 All features are free during beta. Pricing will be introduced later.
          </p>
        </div>
      )}
    </div>
  );
}
