"use client";

import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
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

export interface FeedbackCollectorRef {
  trackTextChange: (oldText: string, newText: string, feedbackType?: FeedbackData['feedback_type'], confidenceScore?: number, processingTime?: number) => void;
  showFeedbackDialog: (feedbackData: FeedbackData) => void;
}

const FeedbackCollector = forwardRef<FeedbackCollectorRef, FeedbackCollectorProps>(({ 
  resumeId, 
  section, 
  context, 
  onFeedbackSubmitted 
}, ref) => {
  const { user } = useAuth();
  const [isCollecting, setIsCollecting] = useState(false);
  const [lastText, setLastText] = useState('');
  const [feedbackQueue, setFeedbackQueue] = useState<FeedbackData[]>([]);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [pendingFeedback, setPendingFeedback] = useState<FeedbackData | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    trackTextChange,
    showFeedbackDialog: (feedbackData: FeedbackData) => {
      setPendingFeedback(feedbackData);
      setShowFeedbackDialog(true);
    }
  }));

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
      section,
      confidence_score: confidenceScore,
      processing_time_ms: processingTime,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent
      }
    };

    // Add to queue for batch processing
    setFeedbackQueue(prev => [...prev, feedbackData]);
  };

  // Submit feedback to backend
  const submitFeedback = async (feedbackData: FeedbackData) => {
    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      const result = await response.json();
      onFeedbackSubmitted?.(result.feedback_id);
      return result;
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  };

  // Process feedback queue periodically
  useEffect(() => {
    if (feedbackQueue.length === 0) return;

    const processQueue = async () => {
      const feedbacksToProcess = [...feedbackQueue];
      setFeedbackQueue([]);

      for (const feedback of feedbacksToProcess) {
        try {
          await submitFeedback(feedback);
        } catch (error) {
          // Re-queue failed feedback
          setFeedbackQueue(prev => [feedback, ...prev]);
        }
      }
    };

    // Debounce processing to avoid too many requests
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(processQueue, 2000);

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [feedbackQueue, onFeedbackSubmitted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div>
      {/* Feedback collection UI */}
      {showFeedbackDialog && pendingFeedback && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Provide Feedback</h3>
            <p className="text-sm text-gray-600 mb-4">
              How would you rate this AI suggestion?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowFeedbackDialog(false);
                  setPendingFeedback(null);
                }}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowFeedbackDialog(false);
                  setPendingFeedback(null);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

FeedbackCollector.displayName = 'FeedbackCollector';

export default FeedbackCollector;