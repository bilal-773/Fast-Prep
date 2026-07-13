import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  TestSession,
  TestSessionSection,
  TestSessionQuestion,
  QuestionCategory,
  UniversityTestConfig,
} from '../lib/supabase'

// ── Derived section state for UI ──────────────────────────────────────────────
export interface SectionState {
  section: TestSessionSection
  category: QuestionCategory
  config: UniversityTestConfig
  questions: TestSessionQuestion[]
  timeRemainingSeconds: number
}

// ── Main store state ──────────────────────────────────────────────────────────
interface ExamStore {
  // Active session
  session: TestSession | null
  sections: SectionState[]
  activeSectionIndex: number   // index into sections[] (current section)
  activeQuestionIndex: number  // index within current section

  // Actions
  setSession: (s: TestSession) => void
  setSections: (sections: SectionState[]) => void
  setActiveSectionIndex: (i: number) => void
  setActiveQuestionIndex: (i: number) => void

  // Answer management
  setAnswer: (sectionId: string, questionId: string, answer: 'A' | 'B' | 'C' | 'D' | null, isCorrect?: boolean | null) => void

  // Timer
  tickTimer: (sectionId: string) => void
  lockSection: (sectionId: string) => void

  // Reset
  clearExam: () => void
}

export const useExamStore = create<ExamStore>()(
  persist(
    (set) => ({
      session: null,
      sections: [],
      activeSectionIndex: 0,
      activeQuestionIndex: 0,

      setSession: (session) => set({ session }),

      setSections: (sections) => set({ sections, activeSectionIndex: 0, activeQuestionIndex: 0 }),

      setActiveSectionIndex: (i) => set({ activeSectionIndex: i, activeQuestionIndex: 0 }),

      setActiveQuestionIndex: (i) => set({ activeQuestionIndex: i }),

      setAnswer: (sectionId, questionId, answer, isCorrect = null) =>
        set((state) => ({
          sections: state.sections.map((s) => {
            if (s.section.id !== sectionId) return s
            return {
              ...s,
              questions: s.questions.map((q) =>
                q.question_id === questionId
                  ? { ...q, student_answer: answer, is_correct: isCorrect, answered_at: new Date().toISOString() }
                  : q
              ),
            }
          }),
        })),

      tickTimer: (sectionId) =>
        set((state) => ({
          sections: state.sections.map((s) => {
            if (s.section.id !== sectionId || s.section.is_locked) return s
            const newTime = Math.max(0, s.timeRemainingSeconds - 1)
            return { ...s, timeRemainingSeconds: newTime }
          }),
        })),

      lockSection: (sectionId) =>
        set((state) => ({
          sections: state.sections.map((s) => {
            if (s.section.id !== sectionId) return s
            return {
              ...s,
              timeRemainingSeconds: 0,
              section: {
                ...s.section,
                is_locked: true,
                locked_at: new Date().toISOString(),
              },
            }
          }),
        })),

      clearExam: () =>
        set({
          session: null,
          sections: [],
          activeSectionIndex: 0,
          activeQuestionIndex: 0,
        }),
    }),
    {
      name: 'fast-exam-store',
      // Only persist essential fields for tab recovery
      partialize: (state) => ({
        session: state.session,
        sections: state.sections,
        activeSectionIndex: state.activeSectionIndex,
        activeQuestionIndex: state.activeQuestionIndex,
      }),
    }
  )
)

// ── Auth store ────────────────────────────────────────────────────────────────
interface AuthStore {
  userId: string | null
  fullName: string | null
  setUser: (id: string | null, name: string | null) => void
}

export const useAuthStore = create<AuthStore>()((set) => ({
  userId: null,
  fullName: null,
  setUser: (userId, fullName) => set({ userId, fullName }),
}))
