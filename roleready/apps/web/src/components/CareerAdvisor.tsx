"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { BookOpen, TrendingUp, Target, CheckCircle, ExternalLink } from 'lucide-react';

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
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Career Growth Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Analyzing your career path...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Career Growth Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={analyzeCareerPath} className="mt-4">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!insights) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Career Growth Plan
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Target className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-4">
              Get personalized career guidance based on your resume
            </p>
            <Button onClick={analyzeCareerPath}>
              Analyze My Career Path
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Career Growth Plan - {getDomainDisplayName(insights.domain)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Alignment Score */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Career Alignment</span>
            <span className={`text-sm font-semibold ${getAlignmentColor(insights.alignment_score)}`}>
              {Math.round(insights.alignment_score * 100)}% - {getAlignmentLabel(insights.alignment_score)}
            </span>
          </div>
          <Progress value={insights.alignment_score * 100} className="h-2" />
        </div>

        {/* Missing Skills */}
        {insights.missing_skills.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">Recommended Skills to Learn</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {insights.missing_skills.slice(0, 6).map((skill, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markSkillCompleted(skill)}
                    className="h-6 w-6 p-0"
                  >
                    {completedSkills.has(skill) ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <div className="h-4 w-4 border-2 border-gray-300 rounded" />
                    )}
                  </Button>
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
              <BookOpen className="h-4 w-4" />
              Recommended Learning Paths
            </h4>
            <div className="space-y-2">
              {insights.learning_paths.slice(0, 4).map((course, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{course.title}</p>
                    <p className="text-xs text-gray-600">{course.platform}</p>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <a href={course.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-3 w-3 mr-1" />
                      View
                    </a>
                  </Button>
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
                <Badge key={index} variant="secondary" className="bg-green-100 text-green-800">
                  {skill}
                </Badge>
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
        <Button variant="outline" onClick={analyzeCareerPath} className="w-full">
          Refresh Analysis
        </Button>
      </CardContent>
    </Card>
  );
}
