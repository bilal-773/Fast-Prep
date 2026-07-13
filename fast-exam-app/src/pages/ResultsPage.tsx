import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { useExamStore } from '../store/examStore'
import type { QuestionCategory } from '../lib/supabase'
import Footer from '../components/Footer'

interface Props {
  sessionId: string
  onRetake: () => void
}

interface SectionResult {
  category: QuestionCategory
  total: number
  attempted: number
  correct: number
  incorrect: number
  skipped: number
  marks: number
  possibleMarks: number
}

export default function ResultsPage({ sessionId, onRetake }: Props) {
  const clearExam = useExamStore((s) => s.clearExam)
  const [results, setResults] = useState<SectionResult[]>([])
  const [loading, setLoading] = useState(true)
  const [showCalculator, setShowCalculator] = useState(false)



  useEffect(() => {
    loadResults()
    clearExam()
  }, [sessionId])

  const loadResults = async () => {
    setLoading(true)
    try {
      // Fetch sections
      const { data: sections } = await supabase
        .from('test_session_sections')
        .select('*, category:question_categories(*)')
        .eq('session_id', sessionId)
        .order('section_order_index')

      // Fetch all session questions with question data
      const { data: tsqs } = await supabase
        .from('test_session_questions')
        .select('*, question:questions(*)')
        .eq('session_id', sessionId)

      // Fetch configs for marks info
      const { data: session } = await supabase
        .from('test_sessions').select('university_id').eq('id', sessionId).single()

      const { data: configs } = await supabase
        .from('university_test_configs')
        .select('*')
        .eq('university_id', session?.university_id ?? '')

      if (!sections || !tsqs || !configs) return

      const sectionResults: SectionResult[] = sections.map((sec) => {
        const cfg = configs.find((c) => c.category_id === sec.category_id)
        const qs = tsqs.filter((q) => q.section_id === sec.id)
        const attempted = qs.filter((q) => q.student_answer !== null)
        const correct  = qs.filter((q) => q.is_correct === true)
        const incorrect = qs.filter((q) => q.is_correct === false)
        const skipped   = qs.filter((q) => q.student_answer === null)
        const marks     = correct.length * (cfg?.marks_per_question ?? 1)

        return {
          category:      sec.category as QuestionCategory,
          total:         qs.length,
          attempted:     attempted.length,
          correct:       correct.length,
          incorrect:     incorrect.length,
          skipped:       skipped.length,
          marks,
          possibleMarks: qs.length * (cfg?.marks_per_question ?? 1),
        }
      })

      setResults(sectionResults)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const totalPossible = results.reduce((s, r) => s + r.possibleMarks, 0)
  const totalCorrect  = results.reduce((s, r) => s + r.correct, 0)





  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Calculating your results...</p>
      </div>
    )
  }

  return (
    <div className="results-page">
      <div className="container animate-fade-in">
        {/* Topbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 24, borderBottom: '1px solid var(--border)', marginBottom: 40 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/logo.svg" alt="FAST Prep Logo" style={{ width: 28, height: 28 }} />
            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1.1rem' }}>FAST Prep — Mock Exam Completed</span>
          </div>
        </div>

        {/* Results Table matching the user's image */}
        <div className="card" style={{ marginBottom: 40, padding: '24px' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textTransform: 'none' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: 600 }}>Subject</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 600 }}>Total Questions</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 600 }}>Attempted</th>
                  <th style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 600 }}>Correct</th>
                </tr>
              </thead>
              <tbody style={{ fontSize: '0.95rem' }}>
                {results.map((r) => {
                  let displayName = r.category.name;
                  if (r.category.slug === 'advanced_math') displayName = 'Advanced Math';
                  else if (r.category.slug === 'basic_math') displayName = 'Basic Math';
                  else if (r.category.slug === 'iq') displayName = 'IQ';
                  
                  return (
                    <tr key={r.category.id} style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                      <td style={{ padding: '14px 8px', textAlign: 'left', fontWeight: 500, color: 'var(--text-primary)' }}>{displayName}</td>
                      <td style={{ padding: '14px 8px', textAlign: 'right' }}>{r.total}</td>
                      <td style={{ padding: '14px 8px', textAlign: 'right' }}>{r.attempted}</td>
                      <td style={{ padding: '14px 8px', textAlign: 'right' }}>{r.correct}</td>
                    </tr>
                  )
                })}
                <tr style={{ fontWeight: 700, color: 'var(--text-primary)', borderTop: '2px solid var(--border)' }}>
                  <td style={{ padding: '16px 8px', textAlign: 'left' }}>Total</td>
                  <td style={{ padding: '16px 8px', textAlign: 'right' }}>{totalPossible}</td>
                  <td style={{ padding: '16px 8px', textAlign: 'right' }}>{results.reduce((s, r) => s + r.attempted, 0)}</td>
                  <td style={{ padding: '16px 8px', textAlign: 'right' }}>{totalCorrect}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Emotion Tagline Heading */}
        <h2 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-heading)', fontWeight: 600, marginBottom: 20, textAlign: 'center', color: 'var(--accent-hover)' }}>
          What would you like to do next?
        </h2>

        {/* Option Cards (The Only 2 Options) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 40 }}>
          {/* Option 1: Calculate Aggregate */}
          <div 
            id="calc-aggregate-option"
            className="card" 
            style={{ 
              cursor: 'pointer', 
              borderColor: showCalculator ? 'var(--accent)' : 'var(--border)',
              background: showCalculator ? 'var(--accent-glow)' : 'var(--bg-surface)',
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
            onClick={() => setShowCalculator(!showCalculator)}
          >
            <div>
              <h3 style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>Calculate Aggregate</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                Let's calculate your aggregate! Check your selection chances at FAST based on this mock test result.
              </p>
            </div>
            <button className="btn btn-secondary" style={{ marginTop: 20, width: '100%', justifyContent: 'center', pointerEvents: 'none' }}>
              {showCalculator ? 'Hide Calculator' : 'Calculate Now'}
            </button>
          </div>

          {/* Option 2: Restart / Retake Exam */}
          <div 
            id="restart-test-option"
            className="card" 
            style={{ 
              cursor: 'pointer', 
              transition: 'all 0.2s ease',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
            onClick={onRetake}
          >
            <div>
              <h3 style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>Start Another Test</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.5 }}>
                Ready to restart the test? Take another attempt with randomized questions to practice more and score higher!
              </p>
            </div>
            <button className="btn btn-primary" style={{ marginTop: 20, width: '100%', justifyContent: 'center', pointerEvents: 'none' }}>
              Restart Mock Test
            </button>
          </div>
        </div>

        {/* Embedded Iframe (displays below the options when Calculate Aggregate is activated) */}
        {showCalculator && (
          <div className="card fade-in" style={{ marginBottom: 60, padding: 0, overflow: 'hidden', border: '1px solid var(--accent)' }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)' }}>
              <h2 style={{ fontSize: '1.1rem', margin: 0, fontFamily: 'var(--font-heading)', fontWeight: 600 }}>
                FAST Admission Aggregate Calculator (Official)
              </h2>
              <a
                href="https://fast-calc-muhammad-bilal.netlify.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              >
                Open Calculator
              </a>
            </div>
            <iframe
              src="https://fast-calc-muhammad-bilal.netlify.app/"
              title="FAST Admission Aggregate Calculator"
              style={{ width: '100%', height: '620px', border: 'none', background: '#070B14' }}
            />
          </div>
        )}
        <Footer />
      </div>
    </div>
  )
}
