"use client";

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface FeedbackInsights {
  total_feedback: number;
  time_period_days: number;
  feedback_by_type: Record<string, number>;
  feedback_by_section: Record<string, number>;
  common_patterns: Record<string, number>;
  model_performance: {
    confidence_correlation: number;
    acceptance_rate_by_confidence: Record<string, number>;
  };
  recommendations: string[];
}

interface FeedbackHistory {
  id: string;
  resume_id: string;
  section: string;
  feedback_type: string;
  timestamp: string;
  confidence_score?: number;
  text_length_ratio: number;
}

interface ModelImprovement {
  type: string;
  priority: string;
  description: string;
  impact: string;
  implementation: string;
}

interface FeedbackStats {
  total_feedback_submitted: number;
  feedback_by_type: Record<string, number>;
  feedback_by_section: Record<string, number>;
  average_confidence_score: number;
  most_common_improvements: string[];
  contribution_score: number;
  last_feedback_date: string;
}

interface FeedbackInsightsProps {
  onClose: () => void;
}

export default function FeedbackInsights({ onClose }: FeedbackInsightsProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'insights' | 'history' | 'improvements' | 'stats'>('insights');
  const [insights, setInsights] = useState<FeedbackInsights | null>(null);
  const [history, setHistory] = useState<FeedbackHistory[]>([]);
  const [improvements, setImprovements] = useState<ModelImprovement[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadInsights();
    }
  }, [user, activeTab]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      
      switch (activeTab) {
        case 'insights':
          const insightsResponse = await fetch('/api/feedback/insights', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
            }
          });
          if (insightsResponse.ok) {
            setInsights(await insightsResponse.json());
          }
          break;
          
        case 'history':
          const historyResponse = await fetch('/api/feedback/history', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
            }
          });
          if (historyResponse.ok) {
            setHistory(await historyResponse.json());
          }
          break;
          
        case 'improvements':
          const improvementsResponse = await fetch('/api/feedback/improvements', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
            }
          });
          if (improvementsResponse.ok) {
            setImprovements(await improvementsResponse.json());
          }
          break;
          
        case 'stats':
          const statsResponse = await fetch('/api/feedback/stats', {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
            }
          });
          if (statsResponse.ok) {
            setStats(await statsResponse.json());
          }
          break;
      }
    } catch (error) {
      console.error('Failed to load feedback data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getFeedbackTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'improvement': return 'text-green-600 bg-green-100';
      case 'manual_edit': return 'text-blue-600 bg-blue-100';
      case 'rejection': return 'text-red-600 bg-red-100';
      case 'rewrite': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Feedback & Model Insights</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex space-x-4 mt-4">
            {[
              { id: 'insights', label: 'Insights' },
              { id: 'history', label: 'History' },
              { id: 'improvements', label: 'Improvements' },
              { id: 'stats', label: 'My Stats' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  activeTab === tab.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-3 text-gray-600">Loading...</span>
            </div>
          ) : (
            <>
              {/* Insights Tab */}
              {activeTab === 'insights' && insights && (
                <div className="space-y-6">
                  {/* Overview */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-blue-800">Total Feedback</h3>
                      <p className="text-2xl font-bold text-blue-900">{insights.total_feedback}</p>
                      <p className="text-sm text-blue-600">Last {insights.time_period_days} days</p>
                    </div>
                    
                    <div className="bg-green-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-green-800">Confidence Correlation</h3>
                      <p className="text-2xl font-bold text-green-900">
                        {Math.round(insights.model_performance.confidence_correlation * 100)}%
                      </p>
                      <p className="text-sm text-green-600">Model accuracy</p>
                    </div>
                    
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-purple-800">Acceptance Rate</h3>
                      <p className="text-2xl font-bold text-purple-900">
                        {Math.round(insights.model_performance.acceptance_rate_by_confidence['high (>0.8)'] * 100)}%
                      </p>
                      <p className="text-sm text-purple-600">High confidence</p>
                    </div>
                  </div>

                  {/* Feedback by Type */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Feedback by Type</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(insights.feedback_by_type).map(([type, count]) => (
                        <div key={type} className="text-center">
                          <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getFeedbackTypeColor(type)}`}>
                            {type.replace('_', ' ')}
                          </div>
                          <p className="text-2xl font-bold mt-2">{count}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Common Patterns */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Common Improvement Patterns</h3>
                    <div className="space-y-3">
                      {Object.entries(insights.common_patterns).map(([pattern, score]) => (
                        <div key={pattern} className="flex items-center justify-between">
                          <span className="text-sm text-gray-700">{pattern.replace(/_/g, ' ')}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-indigo-600 h-2 rounded-full" 
                                style={{ width: `${score * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium text-gray-900">
                              {Math.round(score * 100)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Model Improvement Recommendations</h3>
                    <ul className="space-y-2">
                      {insights.recommendations.map((recommendation, index) => (
                        <li key={index} className="flex items-start space-x-3">
                          <div className="flex-shrink-0 w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center">
                            <span className="text-indigo-600 text-sm font-medium">{index + 1}</span>
                          </div>
                          <p className="text-sm text-gray-700">{recommendation}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* History Tab */}
              {activeTab === 'history' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Your Feedback History</h3>
                  {history.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No feedback history available</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div key={item.id} className="bg-white border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getFeedbackTypeColor(item.feedback_type)}`}>
                                {item.feedback_type.replace('_', ' ')}
                              </span>
                              <span className="text-sm text-gray-600">{item.section}</span>
                              <span className="text-sm text-gray-500">
                                {new Date(item.timestamp).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              {item.confidence_score && (
                                <span className="text-sm text-gray-500">
                                  Confidence: {Math.round(item.confidence_score * 100)}%
                                </span>
                              )}
                              <span className="text-sm text-gray-500">
                                Ratio: {item.text_length_ratio.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Improvements Tab */}
              {activeTab === 'improvements' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Model Improvement Recommendations</h3>
                  <div className="space-y-4">
                    {improvements.map((improvement, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="text-lg font-medium text-gray-900">{improvement.description}</h4>
                            <p className="text-sm text-gray-600 mt-1">{improvement.type.replace('_', ' ')}</p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(improvement.priority)}`}>
                            {improvement.priority} priority
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1">Expected Impact</h5>
                            <p className="text-sm text-gray-600">{improvement.impact}</p>
                          </div>
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1">Implementation</h5>
                            <p className="text-sm text-gray-600">{improvement.implementation}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Stats Tab */}
              {activeTab === 'stats' && stats && (
                <div className="space-y-6">
                  {/* Personal Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-indigo-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-indigo-800">Total Contributions</h3>
                      <p className="text-2xl font-bold text-indigo-900">{stats.total_feedback_submitted}</p>
                      <p className="text-sm text-indigo-600">Feedback records</p>
                    </div>
                    
                    <div className="bg-green-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-green-800">Contribution Score</h3>
                      <p className="text-2xl font-bold text-green-900">{stats.contribution_score}</p>
                      <p className="text-sm text-green-600">Out of 100</p>
                    </div>
                    
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h3 className="text-sm font-medium text-blue-800">Avg Confidence</h3>
                      <p className="text-2xl font-bold text-blue-900">
                        {Math.round(stats.average_confidence_score * 100)}%
                      </p>
                      <p className="text-sm text-blue-600">Model confidence</p>
                    </div>
                  </div>

                  {/* Feedback Breakdown */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Your Feedback Breakdown</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">By Type</h4>
                        <div className="space-y-2">
                          {Object.entries(stats.feedback_by_type).map(([type, count]) => (
                            <div key={type} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">{type.replace('_', ' ')}</span>
                              <span className="text-sm font-medium text-gray-900">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">By Section</h4>
                        <div className="space-y-2">
                          {Object.entries(stats.feedback_by_section).map(([section, count]) => (
                            <div key={section} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">{section}</span>
                              <span className="text-sm font-medium text-gray-900">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Common Improvements */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold mb-4">Your Common Improvements</h3>
                    <ul className="space-y-2">
                      {stats.most_common_improvements.map((improvement, index) => (
                        <li key={index} className="flex items-center space-x-3">
                          <div className="flex-shrink-0 w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                            <span className="text-green-600 text-sm font-medium">{index + 1}</span>
                          </div>
                          <p className="text-sm text-gray-700">{improvement}</p>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <strong>Last feedback:</strong> {new Date(stats.last_feedback_date).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-blue-600 mt-1">
                      Thank you for contributing to our model improvement! Your feedback helps make RoleReady better for everyone.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
