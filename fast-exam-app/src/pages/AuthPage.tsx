import React, { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuthStore } from '../store/examStore'


interface Props {
  onAuth: () => void
}

export default function AuthPage({ onAuth }: Props) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const setUser = useAuthStore((s) => s.setUser)

  const reqMinLength = password.length >= 6
  const reqUppercase = /[A-Z]/.test(password)
  const reqNumber    = /[0-9]/.test(password)
  const reqSpecial   = /[!@#$%^&*(),.?":{}|<>]/.test(password)

  let strength = 'Weak'
  let strengthColor = 'var(--danger)'
  let strengthPercent = '25%'
  
  const score = [reqMinLength, reqUppercase, reqNumber, reqSpecial].filter(Boolean).length
  if (score === 2) {
    strength = 'Fair'
    strengthColor = 'var(--warning)'
    strengthPercent = '50%'
  } else if (score === 3) {
    strength = 'Good'
    strengthColor = 'var(--accent-hover)'
    strengthPercent = '75%'
  } else if (score === 4) {
    strength = 'Strong'
    strengthColor = 'var(--success)'
    strengthPercent = '100%'
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(''); setSuccess(''); 

    if (mode === 'signup' && score < 4) {
      setError('Please fulfill all password requirements first.')
      return
    }

    setLoading(true)

    try {
      if (mode === 'signup') {
        const { data, error: err } = await supabase.auth.signUp({
          email, password,
          options: { data: { full_name: name } }
        })
        if (err) throw err
        if (data.user) {
          setSuccess('Account created! You can now log in.')
          setMode('login')
          setPassword('')
        }
      } else {
        const { data, error: err } = await supabase.auth.signInWithPassword({ email, password })
        if (err) throw err
        if (data.user) {
          // fetch profile
          const { data: profile } = await supabase
            .from('profiles').select('full_name').eq('id', data.user.id).single()
          setUser(data.user.id, profile?.full_name ?? data.user.email ?? null)
          onAuth()
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-layout">
      {/* Left panel - branding, quote, features & arch image */}
      <div className="auth-left">
        <div className="auth-left-content">
          <h1 className="promo-title">
            Prepare.<br />
            <span className="gradient-text-blue">Practice.</span><br />
            <span className="gradient-text-purple">Perform.</span>
          </h1>
          <p className="promo-subtitle">
            Your journey to success starts with consistent practice.
          </p>

          <div className="features-list">
            <div className="feature-item">
              <div className="feature-icon-wrapper">
                <svg className="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="feature-title" style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>Mock Tests</h4>
                <p className="feature-desc" style={{ margin: '2px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Real exam environment</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon-wrapper">
                <svg className="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h4 className="feature-title" style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>Performance Analytics</h4>
                <p className="feature-desc" style={{ margin: '2px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Track and improve</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon-wrapper">
                <svg className="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5a2 2 0 10-2 2h2zm-2 4h4M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8" />
                </svg>
              </div>
              <div>
                <h4 className="feature-title" style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>Achieve Goals</h4>
                <p className="feature-desc" style={{ margin: '2px 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Success is the result</p>
              </div>
            </div>
          </div>

          <div className="quote-block">
            <p className="quote-text">
              "The expert in anything was once a beginner."
            </p>
            <p className="quote-author">— Helen Hayes</p>
          </div>
        </div>
      </div>

      {/* Right panel - Glassmorphic card & custom inputs */}
      <div className="auth-right">
        {/* Background decorations */}
        <div className="bg-glow-circle circle-1" />
        <div className="bg-glow-circle circle-2" />
        <div className="bg-grid-pattern" />

        <div className="auth-card card premium-glass">
          {/* Logo */}
          <div className="auth-logo">
            <img src="/logo.svg" alt="FAST Prep Logo" style={{ width: 44, height: 44 }} />
            <div>
              <div style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1.2rem', letterSpacing: '0.5px' }}>
                FAST Prep
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Entry Test Practice Platform
              </div>
            </div>
          </div>

          <h2 style={{ marginBottom: '8px', fontSize: '1.4rem', fontWeight: 700 }}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '24px' }}>
            {mode === 'login'
              ? 'Sign in to access your mock tests'
              : 'Start practicing for FAST entry test'}
          </p>

          {error && (
            <div style={{
              background: 'var(--danger-glow)', border: '1px solid #EF444430',
              borderRadius: 'var(--radius-md)', padding: '12px 16px',
              color: 'var(--danger)', fontSize: '0.88rem', marginBottom: '16px'
            }}>
              {error}
            </div>
          )}
          {success && (
            <div style={{
              background: 'var(--success-glow)', border: '1px solid #10B98130',
              borderRadius: 'var(--radius-md)', padding: '12px 16px',
              color: 'var(--success)', fontSize: '0.88rem', marginBottom: '16px'
            }}>
              {success}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            {mode === 'signup' && (
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <div className="input-with-icon">
                  <div className="input-icon-left">
                    <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <input
                    id="auth-name"
                    type="text"
                    placeholder="Muhammad Bilal"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}
            
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className="input-with-icon">
                <div className="input-icon-left">
                  <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <input
                  id="auth-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="input-with-icon">
                <div className="input-icon-left">
                  <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  className="input-icon-right"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  {showPassword ? (
                    <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                    </svg>
                  ) : (
                    <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Remember me & Forgot Password */}
            {mode === 'login' && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', marginTop: '2px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                  <input type="checkbox" className="remember-checkbox" />
                  Remember me
                </label>
                <a 
                  href="#" 
                  onClick={(e) => { e.preventDefault(); alert("For credentials reset, please email bilal0420asif@gmail.com"); }} 
                  style={{ color: 'var(--accent-hover)', textDecoration: 'none', fontWeight: 500 }}
                >
                  Forgot password?
                </a>
              </div>
            )}

            {/* Dynamic Password Strength Feedback on Sign-up */}
            {mode === 'signup' && password.length > 0 && (
              <div style={{ marginTop: '4px', animation: 'fadeIn 0.2s ease' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Password Strength:</span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: strengthColor }}>{strength}</span>
                </div>
                <div style={{ height: '4px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden', marginBottom: '12px' }}>
                  <div style={{ height: '100%', width: strengthPercent, background: strengthColor, borderRadius: '2px', transition: 'width 0.2s ease' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: reqMinLength ? 'var(--success)' : 'var(--danger)' }}>{reqMinLength ? '[x]' : '[ ]'}</span> 6+ characters
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: reqUppercase ? 'var(--success)' : 'var(--danger)' }}>{reqUppercase ? '[x]' : '[ ]'}</span> Uppercase letter
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: reqNumber ? 'var(--success)' : 'var(--danger)' }}>{reqNumber ? '[x]' : '[ ]'}</span> A number
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: reqSpecial ? 'var(--success)' : 'var(--danger)' }}>{reqSpecial ? '[x]' : '[ ]'}</span> Special character
                  </div>
                </div>
              </div>
            )}

            {/* Animated Gradient Button */}
            <button
              id="auth-submit"
              type="submit"
              className="btn btn-primary btn-gradient"
              disabled={loading}
              style={{ marginTop: '16px' }}
            >
              {loading ? (
                <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Loading...</>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <svg style={{ width: 16, height: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </span>
              )}
            </button>
          </form>

          <div className="auth-divider" style={{ marginTop: '24px' }}>
            {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
            {' '}
            <button
              className="btn-ghost"
              style={{ padding: '0', color: 'var(--accent-hover)', background: 'none', fontSize: '0.88rem', fontWeight: 600 }}
              onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); setSuccess(''); setPassword('') }}
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </div>
        </div>

        {/* Custom Footer attribution centered beneath layout */}
        <footer className="auth-footer-clean">
          <div>Made by Muhammad Bilal — FAST University</div>
          <div className="footer-social-icons">
            <a href="https://github.com/bilal-773" target="_blank" rel="noopener noreferrer" title="GitHub">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
            <a href="https://www.linkedin.com/in/muhammad-bilal-8b8133335/" target="_blank" rel="noopener noreferrer" title="LinkedIn">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
              </svg>
            </a>
          </div>
        </footer>
      </div>
    </div>
  )
}
