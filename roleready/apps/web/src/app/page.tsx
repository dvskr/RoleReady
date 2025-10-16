import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">RoleReady</h1>
      <p className="mb-6">AI-powered resume optimization and job matching platform.</p>
      
      <div className="space-y-4">
        <Link 
          href="/dashboard" 
          className="block px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Go to Dashboard
        </Link>
        
        <Link 
          href="/login" 
          className="block px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Sign In
        </Link>
        
        <Link 
          href="/dashboard/upload" 
          className="block px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-700"
        >
          Upload Resume
        </Link>
      </div>
    </div>
  )
}