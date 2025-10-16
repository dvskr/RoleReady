"use client";

import Link from "next/link";
import { Trends } from "@/components/Trends";
import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabaseClient";

interface Resume {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  parent_id?: string;
}

export default function DashboardPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('resumes')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false });

      if (error) {
        console.error('Error fetching resumes:', error);
      } else {
        setResumes(data || []);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewResume = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data, error } = await supabase
        .from('resumes')
        .insert({
          title: 'New Resume',
          content: 'Enter your resume content here...',
          user_id: user.id
        })
        .select()
        .single();

      if (error) {
        console.error('Error creating resume:', error);
      } else {
        window.location.href = `/dashboard/editor?id=${data.id}`;
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const shareResume = async (resumeId: string) => {
    const email = prompt("Enter collaborator email:");
    const role = prompt("Select role (viewer/commenter/editor):", "viewer");
    
    if (!email || !role) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/collab/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          resume_id: resumeId,
          email: email,
          role: role
        })
      });

      if (response.ok) {
        alert('Invite sent successfully!');
      } else {
        alert('Error sending invite');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error sending invite');
    }
  };

  return (
    <div className="py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome to Role Ready
            </h1>
            <p className="text-lg text-gray-600">
              Manage your resumes and collaborate with others
            </p>
          </div>
          <button
            onClick={createNewResume}
            className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
          >
            New Resume
          </button>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                My Resumes
              </h2>
              
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading resumes...</p>
                </div>
              ) : resumes.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-4">No resumes yet. Create your first resume!</p>
                  <button
                    onClick={createNewResume}
                    className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Create Resume
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {resumes.map((resume) => (
                    <div key={resume.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-1">
                            {resume.title}
                          </h3>
                          <p className="text-sm text-gray-600 mb-2">
                            {resume.content.length > 100 
                              ? `${resume.content.substring(0, 100)}...` 
                              : resume.content}
                          </p>
                          <p className="text-xs text-gray-500">
                            Updated: {new Date(resume.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex space-x-2 ml-4">
                          <Link
                            href={`/dashboard/editor?id=${resume.id}`}
                            className="bg-blue-600 text-white py-1 px-3 rounded text-sm hover:bg-blue-700 transition-colors"
                          >
                            Edit
                          </Link>
                          <button
                            onClick={() => shareResume(resume.id)}
                            className="bg-green-600 text-white py-1 px-3 rounded text-sm hover:bg-green-700 transition-colors"
                          >
                            Share
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Quick Actions
              </h2>
              <div className="space-y-3">
                <Link
                  href="/dashboard/upload"
                  className="block w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors text-center"
                >
                  Upload Document
                </Link>
                <button
                  onClick={createNewResume}
                  className="block w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors"
                >
                  Create New Resume
                </button>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors text-center"
                >
                  API Documentation
                </a>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Analytics Trends
              </h2>
              <Trends data={[]} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
