"use client";

import React, { useState, useEffect } from 'react';

interface CareerInsight {
  domain: string;
  alignment_score: number;
  missing_skills: string[];
  recommended_skills: string[];
  learning_paths: Array<{
    title: string;
    platform: string;
    url: string;
  }>;
  skill_gaps: {
    missing: string[];
    weak: string[];
    strong: string[];
  };
}

interface CareerAdvisorProps {
  resumeId: string;
  resumeContent: {
    summary: string;
    skills: string[];
    experience: string[];
  };
  onUpdateProgress?: (skillDomain: string, completedSkills: string[]) => void;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function CareerAdvisor({ resumeId, resumeContent, onUpdateProgress }: CareerAdvisorProps) {
  const [insights, setInsights] = useState<CareerInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completedSkills, setCompletedSkills] = useState<Set<string>>(new Set());

  const analyzeCareerPath = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API}/step10/advisor`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          resume_id: resumeId,
          resume_content: resumeContent
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze career path');
      }

      const data = await response.json();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const markSkillCompleted = (skill: string) => {
    const newCompleted = new Set(completedSkills);
    newCompleted.add(skill);
    setCompletedSkills(newCompleted);
    
    // Notify parent component
    if (onUpdateProgress && insights) {
      onUpdateProgress(insights.domain, Array.from(newCompleted));
    }
  };

  const getDomainDisplayName = (domain: string) => {
    const domainNames: Record<string, string> = {
      'data_science': 'Data Science',
      'software_engineering': 'Software Engineering',
      'product_management': 'Product Management',
      'marketing': 'Marketing'
    };
    return domainNames[domain] || domain.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getAlignmentColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAlignmentLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Fair';
    return 'Needs Improvement';
  };

  useEffect(() => {
    if (resumeId && resumeContent && Object.keys(resumeContent).length > 0) {
      analyzeCareerPath();
    }
  }, [resumeId, resumeContent]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 w-full">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
          <h3 className="font-bold text-gray-900">Career Growth Plan</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Analyzing your career path...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 w-full">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
          <h3 className="font-bold text-gray-900">Career Growth Plan</h3>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
          <p className="text-red-700">{error}</p>
        </div>
        <button 
          onClick={analyzeCareerPath}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 w-full">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
          <h3 className="font-bold text-gray-900">Career Growth Plan</h3>
        </div>
        <div className="text-center py-8">
          <div className="w-12 h-12 mx-auto bg-gray-100 rounded-full mb-4 flex items-center justify-center">
            <span className="text-gray-600 text-xl">🎯</span>
          </div>
          <p className="text-gray-600 mb-4">
            Get personalized career guidance based on your resume
          </p>
          <button 
            onClick={analyzeCareerPath}
            className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Analyze My Career Path
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 w-full">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-5 h-5 bg-blue-600 rounded-full"></div>
        <h3 className="font-bold text-gray-900">
          Career Growth Plan - {getDomainDisplayName(insights.domain)}
        </h3>
      </div>
      
      <div className="space-y-6">
        {/* Alignment Score */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Career Alignment</span>
            <span className={`text-sm font-semibold ${getAlignmentColor(insights.alignment_score)}`}>
              {Math.round(insights.alignment_score * 100)}% - {getAlignmentLabel(insights.alignment_score)}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${insights.alignment_score * 100}%` }}
            />
          </div>
        </div>

        {/* Missing Skills */}
        {insights.missing_skills.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">Recommended Skills to Learn</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {insights.missing_skills.slice(0, 6).map((skill, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                  <button
                    onClick={() => markSkillCompleted(skill)}
                    className="h-6 w-6 p-0 border-2 rounded flex items-center justify-center hover:bg-blue-100 transition-colors"
                  >
                    {completedSkills.has(skill) ? (
                      <span className="text-green-600 text-sm">✓</span>
                    ) : (
                      <span className="text-gray-400 text-sm">○</span>
                    )}
                  </button>
                  <span className="text-sm">{skill}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Learning Paths */}
        {insights.learning_paths.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm flex items-center gap-2">
              <span className="text-lg">📚</span>
              Recommended Learning Paths
            </h4>
            <div className="space-y-2">
              {insights.learning_paths.slice(0, 4).map((course, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{course.title}</p>
                    <p className="text-xs text-gray-600">{course.platform}</p>
                  </div>
                  <a 
                    href={course.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 text-xs font-medium border border-blue-200 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                  >
                    View →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skill Gap Analysis */}
        {insights.skill_gaps.strong.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">Your Strengths</h4>
            <div className="flex flex-wrap gap-1">
              {insights.skill_gaps.strong.slice(0, 8).map((skill, index) => (
                <span key={index} className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Action Items */}
        <div className="pt-4 border-t">
          <h4 className="font-semibold text-sm mb-3">Next Steps</h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <div className="h-2 w-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
              <span>Focus on learning the top 3 missing skills to improve your alignment by 25%</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-2 w-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
              <span>Complete at least one recommended course to strengthen your profile</span>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-2 w-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
              <span>Update your resume with new skills as you learn them</span>
            </div>
          </div>
        </div>

        {/* Refresh Button */}
        <button 
          onClick={analyzeCareerPath}
          className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors border border-gray-300"
        >
          Refresh Analysis
        </button>
      </div>
    </div>
  );
}