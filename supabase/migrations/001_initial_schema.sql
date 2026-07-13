-- ============================================================
-- FAST Mock Exam App — Initial Schema Migration
-- Scalable for multi-university future expansion
-- ============================================================

-- 1. Universities table
create table if not exists universities (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  logo_url text,
  is_active boolean default true,
  created_at timestamptz default now()
);

-- 2. Question Categories
create table if not exists question_categories (
  id uuid primary key default gen_random_uuid(),
  university_id uuid references universities(id) on delete cascade,
  name text not null,
  slug text not null,
  created_at timestamptz default now(),
  unique(university_id, slug)
);

-- 3. University Test Configs (drives section counts + timers dynamically)
create table if not exists university_test_configs (
  id uuid primary key default gen_random_uuid(),
  university_id uuid references universities(id) on delete cascade,
  category_id uuid references question_categories(id) on delete cascade,
  question_count int not null,
  time_minutes int not null,
  marks_per_question numeric(4,2) default 1.0,
  negative_marks numeric(4,2) default 0.0
);

-- 4. Profiles (linked to Supabase auth users)
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role text default 'student' check (role in ('student', 'admin')),
  created_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'full_name');
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 5. Questions bank
create table if not exists questions (
  id uuid primary key default gen_random_uuid(),
  university_id uuid references universities(id) on delete cascade,
  category_id uuid references question_categories(id) on delete cascade,
  question_text text not null,
  option_a text not null,
  option_b text not null,
  option_c text not null,
  option_d text not null,
  correct_option char(1) check (correct_option in ('A','B','C','D')),
  explanation text,
  year int,
  is_published boolean default true,
  is_verified boolean default false,
  created_at timestamptz default now()
);

-- 6. Test Sessions
create table if not exists test_sessions (
  id uuid primary key default gen_random_uuid(),
  student_id uuid references profiles(id) on delete cascade,
  university_id uuid references universities(id) on delete cascade,
  status text default 'in_progress' check (status in ('in_progress','submitted','timed_out')),
  section_order jsonb not null,  -- randomized array of category_ids
  total_marks numeric(6,2),
  total_possible numeric(6,2),
  started_at timestamptz default now(),
  submitted_at timestamptz,
  created_at timestamptz default now()
);

-- 7. Test Session Sections (per-section independent timer + lock state)
create table if not exists test_session_sections (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references test_sessions(id) on delete cascade,
  category_id uuid references question_categories(id) on delete cascade,
  section_order_index int not null,
  section_started_at timestamptz,
  time_limit_minutes int not null,
  is_locked boolean default false,
  locked_at timestamptz
);

-- 8. Test Session Questions (frozen snapshot — one row per question per session)
create table if not exists test_session_questions (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references test_sessions(id) on delete cascade,
  section_id uuid references test_session_sections(id) on delete cascade,
  question_id uuid references questions(id) on delete cascade,
  question_order int not null,
  student_answer char(1) check (student_answer in ('A','B','C','D')),
  is_correct boolean,
  marks_awarded numeric(4,2) default 0,
  answered_at timestamptz
);

-- Indexes
create index if not exists idx_questions_university_category on questions(university_id, category_id);
create index if not exists idx_questions_published on questions(is_published);
create index if not exists idx_test_sessions_student on test_sessions(student_id);
create index if not exists idx_tsq_session on test_session_questions(session_id);
create index if not exists idx_tss_session on test_session_sections(session_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table profiles enable row level security;
alter table test_sessions enable row level security;
alter table test_session_sections enable row level security;
alter table test_session_questions enable row level security;
alter table questions enable row level security;
alter table universities enable row level security;
alter table question_categories enable row level security;
alter table university_test_configs enable row level security;

-- Public read for universities, categories, configs, published questions
create policy "Public read universities" on universities for select using (is_active = true);
create policy "Public read categories" on question_categories for select using (true);
create policy "Public read configs" on university_test_configs for select using (true);
create policy "Public read published questions" on questions for select using (is_published = true);

-- Students manage their own profile and sessions
create policy "Student reads own profile" on profiles for select using (auth.uid() = id);
create policy "Student updates own profile" on profiles for update using (auth.uid() = id);

create policy "Student reads own sessions" on test_sessions for select using (auth.uid() = student_id);
create policy "Student inserts own sessions" on test_sessions for insert with check (auth.uid() = student_id);
create policy "Student updates own sessions" on test_sessions for update using (auth.uid() = student_id);

create policy "Student reads own sections" on test_session_sections for select using (
  session_id in (select id from test_sessions where student_id = auth.uid())
);
create policy "Student inserts own sections" on test_session_sections for insert with check (
  session_id in (select id from test_sessions where student_id = auth.uid())
);
create policy "Student updates own sections" on test_session_sections for update using (
  session_id in (select id from test_sessions where student_id = auth.uid())
);

create policy "Student reads own questions" on test_session_questions for select using (
  session_id in (select id from test_sessions where student_id = auth.uid())
);
create policy "Student inserts own questions" on test_session_questions for insert with check (
  session_id in (select id from test_sessions where student_id = auth.uid())
);
create policy "Student updates own answers" on test_session_questions for update using (
  session_id in (select id from test_sessions where student_id = auth.uid())
);
