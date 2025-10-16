"use client";

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface FeedbackData {
  resume_id: string;
  old_text: string;
  new_text: string;
  feedback_type: 'manual_edit' | 'rejection' | 'improvement' | 'rewrite';
  section?: string;
  confidence_score?: number;
  processing_time_ms?: number;
  context?: Record<string, any>;
}

interface FeedbackCollectorProps {
  resumeId?: string;
  section?: string;
  context?: Record<string, any>;
  onFeedbackSubmitted?: (feedbackId: string) => void;
}

export default function FeedbackCollector({ 
  resumeId, 
  section, 
  context, 
  onFeedbackSubmitted 
}: FeedbackCollectorProps) {
  const { user } = useAuth();
  const [isCollecting, setIsCollecting] = useState(false);
  const [lastText, setLastText] = useState('');
  const [feedbackQueue, setFeedbackQueue] = useState<FeedbackData[]>([]);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [pendingFeedback, setPendingFeedback] = useState<FeedbackData | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout>();

  // Track text changes for feedback collection
  const trackTextChange = (
    oldText: string, 
    newText: string, 
    feedbackType: FeedbackData['feedback_type'] = 'manual_edit',
    confidenceScore?: number,
    processingTime?: number
  ) => {
    if (!user || !resumeId || oldText === newText) return;

    const feedbackData: FeedbackData = {
      resume_id: resumeId,
      old_text: oldText,
      new_text: newText,
      feedback_type: feedbackType,
      section: section,
      confidence_score: confidenceScore,
      processing_time_ms: processingTime,
      context: context
    };

    // Add to queue
    setFeedbackQueue(prev => [...prev, feedbackData]);

    // Debounce submission
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      submitFeedbackBatch();
    }, 2000); // Submit after 2 seconds of inactivity
  };

  const submitFeedbackBatch = async () => {
    if (feedbackQueue.length === 0 || !user) return;

    try {
      setIsCollecting(true);
      
      const response = await fetch('/api/feedback/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        },
        body: JSON.stringify(feedbackQueue)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Feedback submitted:', result.feedback_ids);
        
        // Clear queue
        setFeedbackQueue([]);
        
        // Notify parent component
        if (onFeedbackSubmitted && result.feedback_ids.length > 0) {
          onFeedbackSubmitted(result.feedback_ids[0]);
        }
      } else {
        console.error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsCollecting(false);
    }
  };

  const showFeedbackDialogForChange = (
    oldText: string, 
    newText: string, 
    feedbackType: FeedbackData['feedback_type']
  ) => {
    if (!user || !resumeId) return;

    setPendingFeedback({
      resume_id: resumeId,
      old_text: oldText,
      new_text: newText,
      feedback_type: feedbackType,
      section: section,
      context: context
    });
    setShowFeedbackDialog(true);
  };

  const submitFeedbackWithConfirmation = async (feedbackData: FeedbackData) => {
    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        },
        body: JSON.stringify(feedbackData)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Feedback submitted with confirmation:', result.feedback_id);
        
        if (onFeedbackSubmitted) {
          onFeedbackSubmitted(result.feedback_id);
        }
        
        setShowFeedbackDialog(false);
        setPendingFeedback(null);
      } else {
        console.error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      // Submit any remaining feedback
      if (feedbackQueue.length > 0) {
        submitFeedbackBatch();
      }
    };
  }, []);

  return (
    <>
      {/* Feedback Dialog */}
      {showFeedbackDialog && pendingFeedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Help Improve Our AI</h3>
            <p className="text-sm text-gray-600 mb-4">
              We noticed you made changes to the AI-generated content. Your feedback helps us improve!
            </p>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What type of change did you make?
              </label>
              <select
                value={pendingFeedback.feedback_type}
                onChange={(e) => setPendingFeedback({
                  ...pendingFeedback,
                  feedback_type: e.target.value as FeedbackData['feedback_type']
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="improvement">Improvement - Made it better</option>
                <option value="manual_edit">Manual Edit - General changes</option>
                <option value="rejection">Rejection - AI suggestion was wrong</option>
                <option value="rewrite">Rewrite - Complete rewrite</option>
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Original Text:
              </label>
              <div className="p-2 bg-gray-100 rounded text-sm max-h-20 overflow-y-auto">
                {pendingFeedback.old_text}
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Version:
              </label>
              <div className="p-2 bg-blue-50 rounded text-sm max-h-20 overflow-y-auto">
                {pendingFeedback.new_text}
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowFeedbackDialog(false);
                  setPendingFeedback(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Skip
              </button>
              <button
                onClick={() => submitFeedbackWithConfirmation(pendingFeedback)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Collection Status */}
      {isCollecting && (
        <div className="fixed bottom-4 right-4 bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          <span className="text-sm">Saving feedback...</span>
        </div>
      )}
    </>
  );
}

// Hook for easy feedback collection
export function useFeedbackCollection(resumeId?: string, section?: string) {
  const feedbackCollectorRef = useRef<{
    trackTextChange: (oldText: string, newText: string, feedbackType?: FeedbackData['feedback_type'], confidenceScore?: number, processingTime?: number) => void;
    showFeedbackDialog: (oldText: string, newText: string, feedbackType?: FeedbackData['feedback_type']) => void;
  }>();

  const trackTextChange = (
    oldText: string, 
    newText: string, 
    feedbackType: FeedbackData['feedback_type'] = 'manual_edit',
    confidenceScore?: number,
    processingTime?: number
  ) => {
    if (feedbackCollectorRef.current) {
      feedbackCollectorRef.current.trackTextChange(oldText, newText, feedbackType, confidenceScore, processingTime);
    }
  };

  const showFeedbackDialog = (
    oldText: string, 
    newText: string, 
    feedbackType: FeedbackData['feedback_type'] = 'manual_edit'
  ) => {
    if (feedbackCollectorRef.current) {
      feedbackCollectorRef.current.showFeedbackDialog(oldText, newText, feedbackType);
    }
  };

  return {
    trackTextChange,
    showFeedbackDialog,
    FeedbackCollectorComponent: (
      <FeedbackCollector 
        resumeId={resumeId} 
        section={section}
        ref={feedbackCollectorRef}
      />
    )
  };
}
