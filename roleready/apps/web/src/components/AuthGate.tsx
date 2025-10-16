"use client"
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [supabaseConfigured, setSupabaseConfigured] = useState(true)
  
  useEffect(() => {
    // Check if Supabase is properly configured
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    
    if (!supabaseUrl || !supabaseKey || supabaseUrl === 'https://demo.supabase.co') {
      setSupabaseConfigured(false)
      setReady(true)
      return
    }
    
    try {
      supabase.auth.getUser().then(({ data }) => { 
        setUser(data.user)
        setReady(true) 
      })
      
      const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => { 
        setUser(session?.user || null)
        setReady(true) 
      })
      
      return () => { 
        sub.subscription.unsubscribe() 
      }
    } catch (error) {
      console.warn('Supabase auth error:', error)
      setSupabaseConfigured(false)
      setReady(true)
    }
  }, [])
  
  if (!ready) return <div className="p-6">Loading…</div>
  
  // If Supabase is not configured, allow access (demo mode)
  if (!supabaseConfigured) {
    return <>{children}</>
  }
  
  if (!user) return (
    <div className="p-6">
      Please <a className="underline" href="/login">sign in</a>.
    </div>
  )
  
  return <>{children}</>
}
