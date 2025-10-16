"use client";

import Link from "next/link";
import { Trends } from "@/components/Trends";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { listResumes, Resume } from "@/lib/resumes";
import { ClientOnly } from "@/components/ClientOnly";
import TeamSwitcher from "@/components/TeamSwitcher";
import APIKeyManager from "@/components/APIKeyManager";
import PlanStatus from "@/components/PlanStatus";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentTeamId, setCurrentTeamId] = useState<string | null>(null);
  const [showAPIKeyManager, setShowAPIKeyManager] = useState(false);

  useEffect(() => {
    if (user) {
      fetchResumes();
    }
  }, [user, currentTeamId]);

  const fetchResumes = async () => {
    try {
      const userResumes = await listResumes();
      // Filter resumes by team if a team is selected
      const filteredResumes = currentTeamId 
        ? userResumes.filter(resume => resume.team_id === currentTeamId)
        : userResumes.filter(resume => !resume.team_id); // Personal resumes
      setResumes(filteredResumes);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewResume = async () => {
    try {
      if (!user) return;

      // For demo purposes, redirect to editor with a new ID
      const newId = 'resume-' + Math.random().toString(36).substr(2, 9);
      window.location.href = `/dashboard/editor?id=${newId}`;
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const shareResume = async (resumeId: string) => {
    // Mock sharing functionality
    const email = prompt("Enter collaborator email:");
    const role = prompt("Select role (viewer/commenter/editor):", "viewer");
    
    if (!email || !role) return;

    // In a real app, this would make an API call
    alert(`Invite sent to ${email} with ${role} role! (Demo mode)`);
  };

  return (
    <ClientOnly fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    }>
      <div className="py-8">
        <div className="max-w-6xl mx-auto px-4">
                 <div className="flex justify-between items-center mb-8">
                   <div>
                     <h1 className="text-3xl font-bold text-gray-900 mb-2">
                       Welcome back, {user?.name}!
                     </h1>
                     <p className="text-lg text-gray-600">
                       Manage your resumes and collaborate with others
                     </p>
                   </div>
                   <div className="flex space-x-3">
                     <button
                       onClick={createNewResume}
                       className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                     >
                       New Resume
                     </button>
                     <button
                       onClick={() => setShowAPIKeyManager(true)}
                       className="bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition-colors"
                     >
                       API Keys
                     </button>
                     <button
                       onClick={logout}
                       className="bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
                     >
                       Logout
                     </button>
                   </div>
                 </div>

                 {/* Team Switcher */}
                 <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                   <TeamSwitcher 
                     currentTeamId={currentTeamId}
                     onTeamChange={setCurrentTeamId}
                   />
                 </div>

                 {/* Plan Status */}
                 <div className="mb-6">
                   <PlanStatus />
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
      
      {/* API Key Manager Modal */}
      {showAPIKeyManager && (
        <APIKeyManager onClose={() => setShowAPIKeyManager(false)} />
      )}
    </ClientOnly>
  );
}
