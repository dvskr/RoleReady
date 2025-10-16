"use client";
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import LoginForm from '@/components/LoginForm';
import { ClientOnly } from '@/components/ClientOnly';

export default function HomePage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <ClientOnly fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      }>
        <LoginForm />
      </ClientOnly>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">RoleReady</h1>
        <div className="text-right">
          <p className="text-sm text-gray-600">Welcome,</p>
          <p className="font-medium">{user.name}</p>
        </div>
      </div>
      
      <p className="mb-6">AI-powered resume optimization and job matching platform.</p>
      
      <div className="space-y-4">
        <Link 
          href="/dashboard" 
          className="block px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Go to Dashboard
        </Link>
        
        <Link 
          href="/dashboard/upload" 
          className="block px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700"
        >
          Upload Resume
        </Link>
        
        <Link 
          href="/dashboard/editor" 
          className="block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Resume Editor
        </Link>
      </div>
    </div>
  );
}