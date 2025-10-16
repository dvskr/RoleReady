"use client";

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface Team {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  member_count: number;
}

interface TeamSwitcherProps {
  currentTeamId?: string;
  onTeamChange: (teamId: string | null) => void;
}

export default function TeamSwitcher({ currentTeamId, onTeamChange }: TeamSwitcherProps) {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');

  useEffect(() => {
    if (user) {
      fetchTeams();
    }
  }, [user]);

  const fetchTeams = async () => {
    try {
      const response = await fetch('/api/teams', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTeams(data);
      }
    } catch (error) {
      console.error('Failed to fetch teams:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTeam = async () => {
    if (!newTeamName.trim()) return;

    try {
      const response = await fetch('/api/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        },
        body: JSON.stringify({
          name: newTeamName,
          description: newTeamDescription || undefined
        })
      });

      if (response.ok) {
        const newTeam = await response.json();
        setTeams([newTeam, ...teams]);
        setNewTeamName('');
        setNewTeamDescription('');
        setShowCreateForm(false);
        onTeamChange(newTeam.id);
      }
    } catch (error) {
      console.error('Failed to create team:', error);
      alert('Failed to create team');
    }
  };

  const handleTeamSelect = (teamId: string | null) => {
    onTeamChange(teamId);
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
        <span className="text-sm text-gray-600">Loading teams...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4">
      <label htmlFor="team-select" className="text-sm font-medium text-gray-700">
        Team:
      </label>
      
      <select
        id="team-select"
        value={currentTeamId || ''}
        onChange={(e) => handleTeamSelect(e.target.value || null)}
        className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
      >
        <option value="">Personal</option>
        {teams.map((team) => (
          <option key={team.id} value={team.id}>
            {team.name} ({team.member_count} members)
          </option>
        ))}
      </select>

      <button
        onClick={() => setShowCreateForm(!showCreateForm)}
        className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
      >
        {showCreateForm ? 'Cancel' : 'New Team'}
      </button>

      {showCreateForm && (
        <div className="absolute top-16 left-0 bg-white border border-gray-300 rounded-md shadow-lg p-4 z-50 min-w-80">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Create New Team</h3>
          
          <div className="space-y-3">
            <div>
              <label htmlFor="team-name" className="block text-sm font-medium text-gray-700">
                Team Name
              </label>
              <input
                type="text"
                id="team-name"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                placeholder="Enter team name"
              />
            </div>

            <div>
              <label htmlFor="team-description" className="block text-sm font-medium text-gray-700">
                Description (optional)
              </label>
              <textarea
                id="team-description"
                value={newTeamDescription}
                onChange={(e) => setNewTeamDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                placeholder="Enter team description"
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={createTeam}
                disabled={!newTeamName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-300"
              >
                Create Team
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
