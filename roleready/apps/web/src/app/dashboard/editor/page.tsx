"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { getResume, updateResume } from "@/lib/resumes";
import { useAuth } from "@/contexts/AuthContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function EditorPage() {
  const { user } = useAuth();
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [alignment, setAlignment] = useState<any>(null);
  const [saving, setSaving] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [analyzing, setAnalyzing] = useState(false);
  const [rewriting, setRewriting] = useState(false);

  const editor = useEditor({
    extensions: [StarterKit],
    content: resumeText,
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      const content = editor.getHTML();
      setResumeText(content);
      saveResume(content);
    },
  });

  useEffect(() => {
    const loadResume = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const resumeId = urlParams.get('id');
      const resumeText = urlParams.get('rt');
      
      if (resumeText) {
        setResumeText(resumeText);
        editor?.commands.setContent(resumeText);
      } else if (resumeId) {
        try {
          const resume = await getResume(resumeId);
          if (resume && resume.content) {
            setResumeText(resume.content);
            editor?.commands.setContent(resume.content);
          }
        } catch (error) {
          console.error('Failed to load resume:', error);
        }
      }
    };

    if (user) {
      loadResume();
    }
  }, [user, editor]);

  const saveResume = async (content: string) => {
    if (!user) return;
    
    setSaving('saving');
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const resumeId = urlParams.get('id');
      
      if (resumeId) {
        await updateResume(resumeId, { content });
      }
      setSaving('saved');
      setTimeout(() => setSaving('idle'), 2000);
    } catch (error) {
      console.error('Failed to save resume:', error);
      setSaving('idle');
    }
  };

  const analyzeAlignment = async () => {
    if (!resumeText || !jdText) return;
    
    setAnalyzing(true);
    try {
      const response = await fetch(`${API}/align`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, job_description: jdText })
      });
      const result = await response.json();
      setAlignment(result);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const rewriteSection = async (section: string) => {
    if (!resumeText || !jdText) return;
    
    setRewriting(true);
    try {
      const response = await fetch(`${API}/rewrite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          resume_text: resumeText, 
          job_description: jdText,
          section: section
        })
      });
      const result = await response.json();
      
      if (result.rewritten_text) {
        editor?.commands.setContent(result.rewritten_text);
        setResumeText(result.rewritten_text);
      }
    } catch (error) {
      console.error('Rewrite failed:', error);
    } finally {
      setRewriting(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Please log in</h1>
          <Link href="/login" className="text-indigo-600 hover:text-indigo-800">
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-indigo-600 hover:text-indigo-800 mr-4">
                ← Back to Dashboard
              </Link>
              <h1 className="text-xl font-semibold text-gray-900">Resume Editor</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {saving === 'saving' && (
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600 mr-2"></div>
                    Saving...
                  </div>
                )}
                {saving === 'saved' && (
                  <div className="text-sm text-green-600">Saved</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Editor */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <div className="prose max-w-none">
                  <EditorContent editor={editor} />
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Job Description Input */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Description</h3>
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job description here to analyze alignment..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <button
                onClick={analyzeAlignment}
                disabled={analyzing || !resumeText || !jdText}
                className="w-full mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {analyzing ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </div>
                ) : (
                  "Analyze Alignment"
                )}
              </button>
            </div>

            {/* Alignment Results */}
            {alignment && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Alignment Score</h3>
                <div className="text-center mb-4">
                  <div className="text-3xl font-bold text-indigo-600 mb-2">
                    {Math.round(alignment.score || 0)}%
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${alignment.score || 0}%` }}
                    ></div>
                  </div>
                </div>
                
                {alignment.missing_keywords && alignment.missing_keywords.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">Missing Keywords</h4>
                    <div className="flex flex-wrap gap-2">
                      {alignment.missing_keywords.slice(0, 10).map((keyword: string, index: number) => (
                        <span key={index} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => rewriteSection('summary')}
                  disabled={rewriting}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {rewriting ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Rewriting...
                    </div>
                  ) : (
                    "AI Rewrite Resume"
                  )}
                </button>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                  Export to PDF
                </button>
                <button className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                  Export to DOCX
                </button>
                <button className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                  Save Snapshot
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}