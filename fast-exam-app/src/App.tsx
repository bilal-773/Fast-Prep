import { useState, useEffect } from 'react'
import { supabase } from './lib/supabase'
import { useAuthStore, useExamStore } from './store/examStore'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import ExamPage from './pages/ExamPage'
import ResultsPage from './pages/ResultsPage'

type View = 'loading' | 'auth' | 'dashboard' | 'exam' | 'results'

export default function App() {
  const [view, setView] = useState<View>('loading')
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  
  const setUser = useAuthStore((s) => s.setUser)
  const session = useExamStore((s) => s.session)
  const clearExam = useExamStore((s) => s.clearExam)

  useEffect(() => {
    checkUser()
  }, [])

  const checkUser = async () => {
    try {
      const { data: { session: supabaseSession } } = await supabase.auth.getSession()
      if (supabaseSession?.user) {
        // fetch profile
        const { data: profile } = await supabase
          .from('profiles')
          .select('full_name')
          .eq('id', supabaseSession.user.id)
          .single()

        setUser(supabaseSession.user.id, profile?.full_name ?? supabaseSession.user.email ?? null)
        
        // Check if there is a persisted active session in store to restore
        if (session && session.status === 'in_progress') {
          setActiveSessionId(session.id)
          setView('exam')
        } else {
          setView('dashboard')
        }
      } else {
        setView('auth')
      }
    } catch (e) {
      console.error('Error checking user session:', e)
      setView('auth')
    }
  }

  const handleSignOut = async () => {
    setView('loading')
    await supabase.auth.signOut()
    setUser(null, null)
    clearExam()
    setView('auth')
  }

  if (view === 'loading') {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Verifying authentication...</p>
      </div>
    )
  }

  if (view === 'auth') {
    return <AuthPage onAuth={() => setView('dashboard')} />
  }

  if (view === 'dashboard') {
    return (
      <DashboardPage
        onStartExam={(sid) => {
          setActiveSessionId(sid)
          setView('exam')
        }}
        onSignOut={handleSignOut}
      />
    )
  }

  if (view === 'exam') {
    return (
      <ExamPage
        sessionId={activeSessionId!}
        onExamComplete={(sid) => {
          setActiveSessionId(sid)
          setView('results')
        }}
      />
    )
  }

  if (view === 'results') {
    return (
      <ResultsPage
        sessionId={activeSessionId!}
        onRetake={() => {
          setActiveSessionId(null)
          setView('dashboard')
        }}
      />
    )
  }

  return null
}
