import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useAuthStore, useExamStore } from '../store/examStore'
import type { UniversityTestConfig, QuestionCategory } from '../lib/supabase'
import Footer from '../components/Footer'

interface Props {
  onStartExam: (sessionId: string) => void
  onSignOut: () => void
}

const FAST_UNIV_ID  = '1ab2082b-b156-4191-82dd-6873f6946614'

// Section display colors
const SECTION_COLORS: Record<string, string> = {
  advanced_math: '#3B82F6',
  basic_math:    '#8B5CF6',
  iq:            '#F59E0B',
  english:       '#10B981',
}

interface SectionInsert {
  session_id: string
  category_id: string
  section_order_index: number
  time_limit_minutes: number
  is_locked: boolean
  _questions?: { id: string }[]
}

export default function DashboardPage({ onStartExam, onSignOut }: Props) {
  const { fullName, userId } = useAuthStore()
  const clearExam = useExamStore((s) => s.clearExam)

  const [configs, setConfigs] = useState<(UniversityTestConfig & { category: QuestionCategory })[]>([])
  const [pastSessions, setPastSessions] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Fetch test configs with categories
      const { data: cfgData } = await supabase
        .from('university_test_configs')
        .select('*, category:question_categories(*)')
        .eq('university_id', FAST_UNIV_ID)

      if (cfgData) setConfigs(cfgData as (UniversityTestConfig & { category: QuestionCategory })[])

      // Count past sessions
      if (userId) {
        const { count } = await supabase
          .from('test_sessions')
          .select('id', { count: 'exact', head: true })
          .eq('student_id', userId)
        setPastSessions(count ?? 0)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleStartExam = async () => {
    if (!userId) return
    setStarting(true); setError('')

    try {
      clearExam()

      // 1. Fetch all categories for FAST
      const { data: categories } = await supabase
        .from('question_categories')
        .select('*')
        .eq('university_id', FAST_UNIV_ID)

      if (!categories || categories.length === 0) throw new Error('No categories found')

      // 2. Fetch test configs
      const { data: testConfigs } = await supabase
        .from('university_test_configs')
        .select('*')
        .eq('university_id', FAST_UNIV_ID)

      if (!testConfigs) throw new Error('No test configs found')

      // 3. Randomize section order
      const shuffled = [...categories].sort(() => Math.random() - 0.5)
      const sectionOrder = shuffled.map((c) => c.id)

      // 4. Create test session
      const { data: session, error: sessionErr } = await supabase
        .from('test_sessions')
        .insert({
          student_id:     userId,
          university_id:  FAST_UNIV_ID,
          status:         'in_progress',
          section_order:  sectionOrder,
        })
        .select()
        .single()

      if (sessionErr || !session) throw sessionErr ?? new Error('Failed to create session')

      // 5. For each section, pick random questions and create section + question records
      const sectionInserts: SectionInsert[] = []
      const questionInserts: object[] = []

      for (let i = 0; i < shuffled.length; i++) {
        const cat = shuffled[i]
        const cfg = testConfigs.find((c) => c.category_id === cat.id)
        if (!cfg) continue

        // Fetch random questions for this category
        const { data: questions } = await supabase
          .from('questions')
          .select('id')
          .eq('category_id', cat.id)
          .eq('is_published', true)

        if (!questions || questions.length === 0) continue

        // Shuffle and pick required count
        const picked = [...questions]
          .sort(() => Math.random() - 0.5)
          .slice(0, cfg.question_count)

        sectionInserts.push({
          session_id:          session.id,
          category_id:         cat.id,
          section_order_index: i,
          time_limit_minutes:  cfg.time_minutes,
          is_locked:           false,
          _questions:          picked
        })
      }

      // 6. Insert sections
      const { data: createdSections, error: secErr } = await supabase
        .from('test_session_sections')
        .insert(sectionInserts.map(({ _questions, ...s }) => s))
        .select()

      if (secErr || !createdSections) throw secErr ?? new Error('Failed to create sections')

      // 7. Build and insert question assignments
      for (let i = 0; i < createdSections.length; i++) {
        const sec = createdSections[i]
        const questions = (sectionInserts[i] as { _questions?: { id: string }[] })._questions ?? []
        questions.forEach((q, idx) => {
          questionInserts.push({
            session_id:     session.id,
            section_id:     sec.id,
            question_id:    q.id,
            question_order: idx + 1,
          })
        })
      }

      const { error: qErr } = await supabase
        .from('test_session_questions')
        .insert(questionInserts)

      if (qErr) throw qErr

      onStartExam(session.id)

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start exam. Please try again.')
    } finally {
      setStarting(false)
    }
  }

  const totalTime = configs.reduce((s, c) => s + c.time_minutes, 0)
  const totalQuestions = configs.reduce((s, c) => s + c.question_count, 0)

  return (
    <div className="dashboard-page">
      {/* Top Bar */}
      <nav className="topbar">
        <div className="container topbar-inner">
          <div className="topbar-brand">
            <div className="topbar-brand-icon" style={{ color: 'white', fontWeight: 'bold', fontSize: '1rem' }}>FP</div>
            <span>FAST Prep</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {fullName ?? 'Student'}
            </span>
            <button id="sign-out-btn" className="btn btn-ghost" onClick={onSignOut}>
              Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-section">
        <div className="container">
          <div className="badge badge-blue" style={{ marginBottom: 20 }}>FAST-NUCES Entry Test</div>
          <h1 className="hero-title">
            Practice Like the<br />Real Thing
          </h1>
          <p className="hero-subtitle">
            Full-length mock tests with randomized sections, independent timers, 
            and detailed performance analytics — exactly like the actual FAST exam.
          </p>

          {error && (
            <div style={{
              background: 'var(--danger-glow)', border: '1px solid #EF444440',
              borderRadius: 'var(--radius-md)', padding: '12px 20px',
              color: 'var(--danger)', fontSize: '0.88rem', marginBottom: '20px',
              display: 'inline-block'
            }}>
              [Error] {error}
            </div>
          )}

          <button
            id="start-exam-btn"
            className="btn btn-primary"
            style={{ fontSize: '1.05rem', padding: '14px 36px' }}
            onClick={handleStartExam}
            disabled={starting || loading}
          >
            {starting
              ? <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Creating your test...</>
              : 'Start Mock Test'}
          </button>

          {pastSessions > 0 && (
            <p style={{ marginTop: 16, color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              You've attempted {pastSessions} mock test{pastSessions !== 1 ? 's' : ''} so far
            </p>
          )}
        </div>
      </section>

      {/* Stats */}
      <div className="container">
        <div className="stats-row">
          <div className="card stat-card">
            <div className="stat-number">{totalQuestions}</div>
            <div className="stat-label">Questions per Test</div>
          </div>
          <div className="card stat-card">
            <div className="stat-number">{totalTime}</div>
            <div className="stat-label">Total Minutes</div>
          </div>
          <div className="card stat-card">
            <div className="stat-number">{configs.length}</div>
            <div className="stat-label">Sections</div>
          </div>
          <div className="card stat-card">
            <div className="stat-number">1132</div>
            <div className="stat-label">Question Bank</div>
          </div>
        </div>

        {/* Section Cards */}
        <h2 style={{ margin: '40px 0 20px', fontSize: '1.3rem' }}>Exam Sections</h2>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
            <div className="spinner" />
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 60 }}>
            {configs.map((cfg) => {
              const color = SECTION_COLORS[cfg.category?.slug ?? ''] ?? 'var(--accent)'
              return (
                <div key={cfg.id} className="card" style={{ borderColor: color + '40' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>{cfg.category?.name}</h3>
                    <span className="badge badge-blue" style={{ borderColor: color + '40', color }}>
                      {cfg.time_minutes} min
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 24 }}>
                    <div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color }}>
                        {cfg.question_count}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Questions</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text-secondary)' }}>
                        {cfg.marks_per_question}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Mark each</div>
                    </div>
                  </div>
                  <div style={{
                    marginTop: 16, padding: '8px 12px',
                    background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)',
                    fontSize: '0.8rem', color: 'var(--text-muted)'
                  }}>
                    Note: Timer is independent and starts when you enter this section
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Rules */}
        <div className="card" style={{ marginBottom: 60 }}>
          <h3 style={{ marginBottom: 16 }}>Exam Rules</h3>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: 10, paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <li>Section order is <strong style={{ color: 'var(--text-primary)' }}>randomized</strong> every attempt</li>
            <li>Each section has its own <strong style={{ color: 'var(--text-primary)' }}>independent timer</strong> — time in one section doesn't affect others</li>
            <li>When a section timer reaches 00:00, it is <strong style={{ color: 'var(--danger)' }}>permanently locked</strong></li>
            <li>You can <strong style={{ color: 'var(--text-primary)' }}>skip questions</strong> and revisit them within the active section</li>
            <li>You <strong>cannot</strong> navigate to other sections while in an active section</li>
            <li>Questions are selected <strong style={{ color: 'var(--text-primary)' }}>randomly</strong> from a bank of 1,132 questions</li>
          </ul>
        </div>
        <Footer />
      </div>
    </div>
  )
}
