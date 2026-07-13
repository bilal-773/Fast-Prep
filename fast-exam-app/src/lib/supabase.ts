import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false
  }
})

// ── Types matching our DB schema ──────────────────────────────────────────────

export interface University {
  id: string
  name: string
  slug: string
  logo_url: string | null
  is_active: boolean
}

export interface QuestionCategory {
  id: string
  university_id: string
  name: string
  slug: string
}

export interface UniversityTestConfig {
  id: string
  university_id: string
  category_id: string
  question_count: number
  time_minutes: number
  marks_per_question: number
  negative_marks: number
}

export interface Question {
  id: string
  university_id: string
  category_id: string
  question_text: string
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  correct_option: 'A' | 'B' | 'C' | 'D' | null
  explanation: string | null
  year: number | null
}

export interface TestSession {
  id: string
  student_id: string
  university_id: string
  status: 'in_progress' | 'submitted' | 'timed_out'
  section_order: string[]   // array of category_ids in randomized order
  total_marks: number | null
  total_possible: number | null
  started_at: string
  submitted_at: string | null
}

export interface TestSessionSection {
  id: string
  session_id: string
  category_id: string
  section_order_index: number
  section_started_at: string | null
  time_limit_minutes: number
  is_locked: boolean
  locked_at: string | null
}

export interface TestSessionQuestion {
  id: string
  session_id: string
  section_id: string
  question_id: string
  question_order: number
  student_answer: 'A' | 'B' | 'C' | 'D' | null
  is_correct: boolean | null
  marks_awarded: number
  answered_at: string | null
  // joined
  question?: Question
}

export interface Profile {
  id: string
  full_name: string | null
  role: 'student' | 'admin'
}
