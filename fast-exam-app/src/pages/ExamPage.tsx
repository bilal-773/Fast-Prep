import { useEffect, useRef, useCallback, useState } from 'react'
import { supabase } from '../lib/supabase'
import { useExamStore, type SectionState } from '../store/examStore'
import type { QuestionCategory, TestSessionQuestion, Question } from '../lib/supabase'

interface Props {
  sessionId: string
  onExamComplete: (sessionId: string) => void
}

export default function ExamPage({ sessionId, onExamComplete }: Props) {
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    description: '',
    onConfirm: () => {},
  })

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const {
    session, sections, activeSectionIndex, activeQuestionIndex,
    setSession, setSections, setActiveSectionIndex, setActiveQuestionIndex,
    setAnswer, tickTimer, lockSection
  } = useExamStore()

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const initialized = useRef(false)

  // ── Load session from DB (handles page refresh) ───────────────────────────
  useEffect(() => {
    if (initialized.current) return
    initialized.current = true
    loadSession()
  }, [sessionId])

  const loadSession = async () => {
    // Fetch session
    const { data: sess } = await supabase
      .from('test_sessions').select('*').eq('id', sessionId).single()
    if (!sess) return
    setSession(sess)

    // Fetch sections + categories + configs
    const { data: secs } = await supabase
      .from('test_session_sections')
      .select('*, category:question_categories(*)')
      .eq('session_id', sessionId)
      .order('section_order_index')

    const { data: configs } = await supabase
      .from('university_test_configs')
      .select('*')
      .eq('university_id', sess.university_id)

    // Fetch all session questions with question data
    const { data: tsqs } = await supabase
      .from('test_session_questions')
      .select('*, question:questions(*)')
      .eq('session_id', sessionId)
      .order('question_order')

    if (!secs || !configs || !tsqs) return

    const now = Date.now()
    const sectionStates: SectionState[] = secs.map((sec) => {
      const cfg = configs.find((c) => c.category_id === sec.category_id)!
      const qs = tsqs.filter((q) => q.section_id === sec.id) as TestSessionQuestion[]

      // Calculate remaining time
      let remaining = cfg.time_minutes * 60
      if (sec.section_started_at && !sec.is_locked) {
        const elapsed = Math.floor((now - new Date(sec.section_started_at).getTime()) / 1000)
        remaining = Math.max(0, remaining - elapsed)
        if (remaining === 0) {
          // Should be locked server-side already
          sec.is_locked = true
        }
      }

      return {
        section: sec,
        category: sec.category as QuestionCategory,
        config: cfg,
        questions: qs,
        timeRemainingSeconds: sec.is_locked ? 0 : remaining,
      }
    })

    setSections(sectionStates)

    // Find the first non-locked section to start on
    const firstActive = sectionStates.findIndex((s) => !s.section.is_locked)
    if (firstActive >= 0) setActiveSectionIndex(firstActive)
    else {
      // All locked = exam over
      await finalizeSession(sess.id, sectionStates)
      onExamComplete(sess.id)
    }
  }

  // ── Timer tick ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current)

    const activeSection = sections[activeSectionIndex]
    if (!activeSection || activeSection.section.is_locked) return

    // Start timer on server if not started
    if (!activeSection.section.section_started_at) {
      startSectionTimer(activeSection)
    }

    timerRef.current = setInterval(() => {
      const s = useExamStore.getState().sections[activeSectionIndex]
      if (!s || s.section.is_locked) { clearInterval(timerRef.current!); return }

      if (s.timeRemainingSeconds <= 1) {
        clearInterval(timerRef.current!)
        handleSectionExpiry(s)
      } else {
        tickTimer(s.section.id)
      }
    }, 1000)

    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [activeSectionIndex, sections.length])

  const startSectionTimer = async (s: SectionState) => {
    const now = new Date().toISOString()
    await supabase
      .from('test_session_sections')
      .update({ section_started_at: now })
      .eq('id', s.section.id)
  }

  const handleSectionExpiry = useCallback(async (s: SectionState) => {
    lockSection(s.section.id)
    await supabase
      .from('test_session_sections')
      .update({ is_locked: true, locked_at: new Date().toISOString() })
      .eq('id', s.section.id)

    // Move to next unlocked section
    const currentSections = useExamStore.getState().sections
    const nextIdx = currentSections.findIndex(
      (sec, i) => i > activeSectionIndex && !sec.section.is_locked
    )

    if (nextIdx >= 0) {
      setActiveSectionIndex(nextIdx)
    } else {
      // Check if all done
      const allLocked = currentSections.every((sec) => sec.section.is_locked)
      if (allLocked && session) {
        await finalizeSession(session.id, currentSections)
        onExamComplete(session.id)
      }
    }
  }, [activeSectionIndex, session])

  const finalizeSession = async (sid: string, sectionStates: SectionState[]) => {
    // Calculate total marks
    let total = 0, possible = 0
    sectionStates.forEach((s) => {
      s.questions.forEach((q) => {
        possible += s.config.marks_per_question
        if (q.is_correct) total += s.config.marks_per_question
      })
    })
    await supabase
      .from('test_sessions')
      .update({ status: 'submitted', submitted_at: new Date().toISOString(), total_marks: total, total_possible: possible })
      .eq('id', sid)
  }

  // ── Save answer to DB ─────────────────────────────────────────────────────
  const handleAnswer = async (tsqId: string, questionId: string, answer: 'A' | 'B' | 'C' | 'D') => {
    const activeSection = sections[activeSectionIndex]
    if (!activeSection || activeSection.section.is_locked) return

    // Guard: reject if section is locked server-side
    const tsq = activeSection.questions.find((q) => q.question_id === questionId)
    if (!tsq) return

    const question = tsq.question as Question
    const isCorrect = question.correct_option ? answer === question.correct_option : null
    const marks = isCorrect ? activeSection.config.marks_per_question : 0

    setAnswer(activeSection.section.id, questionId, answer, isCorrect)

    await supabase
      .from('test_session_questions')
      .update({
        student_answer: answer,
        is_correct:     isCorrect,
        marks_awarded:  marks,
        answered_at:    new Date().toISOString(),
      })
      .eq('id', tsqId)
  }

  const handleSkip = () => {
    const s = sections[activeSectionIndex]
    if (!s) return
    if (activeQuestionIndex < s.questions.length - 1) {
      setActiveQuestionIndex(activeQuestionIndex + 1)
    }
  }

  const handleSubmitSection = () => {
    const s = sections[activeSectionIndex]
    if (!s) return
    setConfirmModal({
      isOpen: true,
      title: `Submit ${s.category.name} Section?`,
      description: 'This will lock this section permanently. You will not be able to change or answer questions in this section again.',
      onConfirm: async () => {
        await handleSectionExpiry(s)
      }
    })
  }

  const handleSubmitExam = () => {
    setConfirmModal({
      isOpen: true,
      title: 'Submit Entire Exam?',
      description: 'Are you sure you want to submit your exam? This will end your mock test session and calculate your results.',
      onConfirm: async () => {
        if (timerRef.current) clearInterval(timerRef.current)
        if (session) {
          await finalizeSession(session.id, sections)
          onExamComplete(session.id)
        }
      }
    })
  }

  // ── Render helpers ────────────────────────────────────────────────────────
  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0')
    const s = (sec % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  const getTimerClass = (sec: number, limit: number) => {
    const pct = sec / (limit * 60)
    if (pct <= 0.1) return 'timer timer-danger'
    if (pct <= 0.25) return 'timer timer-warning'
    return 'timer timer-normal'
  }

  const activeSection = sections[activeSectionIndex]
  const activeQuestion = activeSection?.questions[activeQuestionIndex] as TestSessionQuestion & { question: Question } | undefined

  if (sections.length === 0) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Loading your exam...</p>
      </div>
    )
  }

  return (
    <div className="exam-layout">
      {/* ── Sidebar Backdrop ───────────────────────────────────────────── */}
      {mobileMenuOpen && (
        <div className="sidebar-backdrop" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* ── Sidebar ───────────────────────────────────────────────────── */}
      <aside className={`exam-sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/logo.svg" alt="FAST Prep Logo" style={{ width: 24, height: 24 }} />
            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '0.9rem' }}>FAST Mock Test</span>
          </div>
          <button 
            type="button"
            className="mobile-close-btn"
            onClick={() => setMobileMenuOpen(false)}
            style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: 4 }}
          >
            <svg style={{ width: 20, height: 20 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {sections.map((s, si) => {
          const isActive = si === activeSectionIndex
          const answered  = s.questions.filter((q) => q.student_answer !== null).length
          const status = s.section.is_locked ? 'locked' : isActive ? 'active' : 'pending'

          return (
            <div
              key={s.section.id}
              className={`section-nav-item ${isActive ? 'active' : ''} ${s.section.is_locked ? 'locked' : ''}`}
            >
              <div 
                className="section-nav-header" 
                onClick={() => {
                  if (!s.section.is_locked) {
                    setActiveSectionIndex(si)
                    setMobileMenuOpen(false)
                  }
                }}
              >
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700 }}>{s.category.name}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    {answered}/{s.questions.length} answered
                  </div>
                </div>
                <div>
                  {status === 'locked' && <span className="badge badge-red">Locked</span>}
                  {status === 'active' && (
                    <span className={getTimerClass(s.timeRemainingSeconds, s.config.time_minutes)}>
                      {formatTime(s.timeRemainingSeconds)}
                    </span>
                  )}
                  {status === 'pending' && <span className="badge badge-gray">Pending</span>}
                </div>
              </div>

              {/* Question grid for active section */}
              {isActive && (
                <div className="question-grid">
                  {s.questions.map((q, qi) => (
                    <div
                      key={q.id}
                      className={`q-bubble ${
                        qi === activeQuestionIndex ? 'active' :
                        q.student_answer !== null ? 'answered' : ''
                      }`}
                      onClick={() => {
                        setActiveQuestionIndex(qi)
                        setMobileMenuOpen(false)
                      }}
                      title={`Question ${qi + 1}`}
                    >
                      {qi + 1}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        <div style={{ marginTop: 'auto' }}>
          <button id="submit-exam-btn" className="btn btn-danger" style={{ width: '100%', justifyContent: 'center' }} onClick={handleSubmitExam}>
            Submit Exam
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <main className="exam-main">
        {/* Header */}
        <div className="exam-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              type="button"
              className="btn btn-secondary mobile-menu-toggle-btn"
              onClick={() => setMobileMenuOpen(true)}
              style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <svg style={{ width: 18, height: 18 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <span style={{ fontSize: '0.8rem' }}>Menu</span>
            </button>
            <div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                Section {activeSectionIndex + 1} of {sections.length}
              </div>
              <h2 style={{ fontSize: '1.1rem' }}>{activeSection?.category.name}</h2>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {activeSection && !activeSection.section.is_locked && (
              <div className={getTimerClass(activeSection.timeRemainingSeconds, activeSection.config.time_minutes)}>
                Time: {formatTime(activeSection.timeRemainingSeconds)}
              </div>
            )}
            <button id="submit-section-btn" className="btn btn-secondary" onClick={handleSubmitSection}>
              Submit Section
            </button>
          </div>
        </div>

        {/* Question */}
        {activeQuestion ? (
          <div className="question-card">
            <div className="question-number">
              Question {activeQuestionIndex + 1} of {activeSection?.questions.length}
            </div>
            <p className="question-text">{activeQuestion.question?.question_text}</p>

            <div className="options-list">
              {(['A', 'B', 'C', 'D'] as const).map((letter) => {
                const text = activeQuestion.question?.[`option_${letter.toLowerCase()}` as 'option_a']
                const isSelected = activeQuestion.student_answer === letter
                const locked = activeSection?.section.is_locked

                return (
                  <div
                    key={letter}
                    id={`option-${letter}`}
                    className={`option-item ${isSelected ? 'selected' : ''} ${locked ? 'disabled' : ''}`}
                    onClick={() => !locked && handleAnswer(activeQuestion.id, activeQuestion.question_id, letter)}
                  >
                    <div className="option-letter">{letter}</div>
                    <div className="option-text">{text}</div>
                  </div>
                )
              })}
            </div>

            {/* Question Actions */}
            <div className="question-actions">
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  id="prev-question-btn"
                  className="btn btn-secondary"
                  disabled={activeQuestionIndex === 0}
                  onClick={() => setActiveQuestionIndex(activeQuestionIndex - 1)}
                >
                  Prev
                </button>
                <button
                  id="skip-question-btn"
                  className="btn btn-ghost"
                  onClick={handleSkip}
                  disabled={activeSection?.section.is_locked}
                >
                  Skip
                </button>
              </div>
              <button
                id="next-question-btn"
                className="btn btn-primary"
                disabled={activeQuestionIndex >= (activeSection?.questions.length ?? 0) - 1}
                onClick={() => setActiveQuestionIndex(activeQuestionIndex + 1)}
              >
                Next
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
            <svg style={{ width: 64, height: 64, color: 'var(--success)', marginBottom: 16 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3>Section Complete</h3>
            <p style={{ marginTop: 8 }}>All questions in this section have been answered.</p>
          </div>
        )}
      </main>

      {confirmModal.isOpen && (
        <div className="confirm-modal-overlay">
          <div className="confirm-modal card">
            <h2>{confirmModal.title}</h2>
            <p>{confirmModal.description}</p>
            <div className="confirm-modal-actions">
              <button 
                className="btn btn-secondary" 
                onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })}
              >
                Cancel
              </button>
              <button 
                className="btn btn-danger" 
                onClick={() => {
                  confirmModal.onConfirm();
                  setConfirmModal({ ...confirmModal, isOpen: false });
                }}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
