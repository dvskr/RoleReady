"use client";

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface APIKey {
  id: string;
  name: string;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
}

interface APIKeyUsage {
  endpoint: string;
  method: string;
  count: number;
  last_used: string;
}

interface APIKeyManagerProps {
  onClose: () => void;
}

export default function APIKeyManager({ onClose }: APIKeyManagerProps) {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpiresDays, setNewKeyExpiresDays] = useState<number | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [keyUsage, setKeyUsage] = useState<APIKeyUsage[]>([]);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchAPIKeys();
    }
  }, [user]);

  const fetchAPIKeys = async () => {
    try {
      const response = await fetch('/api/api-keys', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data);
      }
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const createAPIKey = async () => {
    if (!newKeyName.trim()) return;

    try {
      const response = await fetch('/api/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        },
        body: JSON.stringify({
          name: newKeyName,
          expires_days: newKeyExpiresDays || undefined
        })
      });

      if (response.ok) {
        const newKey = await response.json();
        setApiKeys([newKey, ...apiKeys]);
        setNewKeyName('');
        setNewKeyExpiresDays(null);
        setShowCreateForm(false);
        setNewlyCreatedKey(newKey.key);
      }
    } catch (error) {
      console.error('Failed to create API key:', error);
      alert('Failed to create API key');
    }
  };

  const deleteAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        }
      });

      if (response.ok) {
        setApiKeys(apiKeys.filter(key => key.id !== keyId));
        if (selectedKey === keyId) {
          setSelectedKey(null);
          setKeyUsage([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete API key:', error);
      alert('Failed to delete API key');
    }
  };

  const regenerateAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to regenerate this API key? The old key will no longer work.')) {
      return;
    }

    try {
      const response = await fetch(`/api/api-keys/${keyId}/regenerate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        }
      });

      if (response.ok) {
        const regeneratedKey = await response.json();
        setApiKeys(apiKeys.map(key => 
          key.id === keyId 
            ? { ...key, created_at: regeneratedKey.created_at }
            : key
        ));
        setNewlyCreatedKey(regeneratedKey.key);
      }
    } catch (error) {
      console.error('Failed to regenerate API key:', error);
      alert('Failed to regenerate API key');
    }
  };

  const fetchKeyUsage = async (keyId: string) => {
    try {
      const response = await fetch(`/api/api-keys/${keyId}/usage`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('roleready_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setKeyUsage(data);
      }
    } catch (error) {
      console.error('Failed to fetch key usage:', error);
    }
  };

  const handleKeySelect = (keyId: string) => {
    setSelectedKey(keyId);
    fetchKeyUsage(keyId);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('API key copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-center text-gray-600">Loading API keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">API Key Management</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex h-96">
          {/* Left Panel - API Keys List */}
          <div className="w-1/2 border-r border-gray-200 p-6 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Your API Keys</h3>
              <button
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
              >
                {showCreateForm ? 'Cancel' : 'New Key'}
              </button>
            </div>

            {showCreateForm && (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Create New API Key</h4>
                <div className="space-y-2">
                  <input
                    type="text"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="API key name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <input
                    type="number"
                    value={newKeyExpiresDays || ''}
                    onChange={(e) => setNewKeyExpiresDays(e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="Expires in days (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                  <button
                    onClick={createAPIKey}
                    disabled={!newKeyName.trim()}
                    className="w-full px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-300 text-sm"
                  >
                    Create Key
                  </button>
                </div>
              </div>
            )}

            {newlyCreatedKey && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="text-sm font-medium text-green-800 mb-2">New API Key Created!</h4>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 bg-white px-2 py-1 rounded text-xs font-mono text-green-800">
                    {newlyCreatedKey}
                  </code>
                  <button
                    onClick={() => copyToClipboard(newlyCreatedKey)}
                    className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
                  >
                    Copy
                  </button>
                </div>
                <p className="text-xs text-green-700 mt-1">
                  ⚠️ Save this key now - you won't be able to see it again!
                </p>
                <button
                  onClick={() => setNewlyCreatedKey(null)}
                  className="text-xs text-green-600 hover:text-green-800 mt-1"
                >
                  Dismiss
                </button>
              </div>
            )}

            <div className="space-y-2">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedKey === key.id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleKeySelect(key.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">{key.name}</h4>
                      <p className="text-xs text-gray-500">
                        Created: {new Date(key.created_at).toLocaleDateString()}
                      </p>
                      {key.last_used_at && (
                        <p className="text-xs text-gray-500">
                          Last used: {new Date(key.last_used_at).toLocaleDateString()}
                        </p>
                      )}
                      {key.expires_at && (
                        <p className="text-xs text-orange-600">
                          Expires: {new Date(key.expires_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          regenerateAPIKey(key.id);
                        }}
                        className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
                      >
                        Regenerate
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteAPIKey(key.id);
                        }}
                        className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {apiKeys.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No API keys found</p>
                <p className="text-sm text-gray-400">Create your first API key to get started</p>
              </div>
            )}
          </div>

          {/* Right Panel - Usage Details */}
          <div className="w-1/2 p-6 overflow-y-auto">
            {selectedKey ? (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Statistics</h3>
                {keyUsage.length > 0 ? (
                  <div className="space-y-3">
                    {keyUsage.map((usage, index) => (
                      <div key={index} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-sm">
                            {usage.method} {usage.endpoint}
                          </span>
                          <span className="text-sm font-medium text-gray-900">
                            {usage.count} calls
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Last used: {new Date(usage.last_used).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No usage data available</p>
                    <p className="text-sm text-gray-400">Start making API calls to see usage statistics</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Select an API key to view usage statistics</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              <p>API keys allow external applications to access your RoleReady data.</p>
              <p>Keep your keys secure and never share them publicly.</p>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
