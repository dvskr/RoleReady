"use client"
import { supabase } from '@/lib/supabaseClient'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const router = useRouter()
  
  return (
    <div className="p-6 max-w-sm mx-auto space-y-3">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <input 
        className="w-full border p-2 rounded" 
        placeholder="Email" 
        value={email} 
        onChange={e => setEmail(e.target.value)} 
      />
      <div className="flex gap-2">
        <button 
          className="px-3 py-2 rounded bg-black text-white" 
          onClick={async () => {
            await supabase.auth.signInWithOtp({ email })
            alert('Check your email for the magic link')
          }}
        >
          Email link
        </button>
        <button 
          className="px-3 py-2 rounded bg-indigo-600 text-white" 
          onClick={async () => {
            const { data, error } = await supabase.auth.signInWithOAuth({ provider: 'google' })
            if (error) alert(error.message)
          }}
        >
          Google
        </button>
      </div>
      <button 
        className="text-sm text-gray-600 underline" 
        onClick={() => router.push('/dashboard')}
      >
        Skip (dev)
      </button>
    </div>
  )
}
