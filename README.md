# Fast-Prep: University Entry Test Preparation App

Fast-Prep is an online mock exam web application designed specifically for students preparing for university entrance tests, with a primary initial focus on the FAST-NUCES admission test. The codebase is designed with database-driven configurations, making it scalable for other universities (such as NUST, UET, etc.) by seeding configuration rows without changing the application logic.

## Project Structure

* **`fast-exam-app/`**: A modern React frontend built with Vite, TypeScript, and Vanilla CSS. It provides a premium, responsive user interface featuring glassmorphic designs, dark mode aesthetics, and micro-animations.
* **`supabase/`**: Contains Supabase database schema and migrations (`supabase/migrations/001_initial_schema.sql`).
* **`scripts/`**: Python utility scripts for database seeding, maintenance, and question operations.
* **`all_questions.json`**: The consolidated, master list of questions used for database seeding.
* **`fastprep_logo_v3.svg`**: Logo asset for the web application.

---

## Core Features

### 1. Section-Based Independent Timers
Each section of the exam has its own independent, strict countdown timer:
* **Advanced Mathematics:** 50 minutes
* **Basic Mathematics:** 20 minutes
* **IQ / Analytical Skills:** 20 minutes
* **English:** 30 minutes

The time spent in one section does not deduct from another. The section timer begins when the student opens that section. Section timers are persisted on the server using `section_started_at` database timestamps, ensuring that if a student refreshes or loses connection, the remaining time is accurately re-evaluated.

### 2. Randomized Section Ordering
The sequence of the exam sections is randomized for every test session.
* The generated order (e.g., IQ → English → Advanced Math → Basic Math) is stored in the database (`section_order` on `test_sessions`) to ensure the sequence remains consistent if a student resumes their session.
* The sidebar navigation displays the generated sequence to the student throughout the exam.

### 3. Section Lockout on Expiry
When a section timer hits `00:00`, the section is locked.
* Stored answers are preserved, and unanswered questions are recorded as skipped (`null`).
* The lockout is enforced both in the frontend UI (disabling selection) and on the backend database policies (blocking save-answer requests).
* Upon lock, the student is automatically transitioned to the next active section.

### 4. Question Skipping and Navigation
* Students can freely skip, revisit, and navigate questions within the active section.
* A filter view shows skipped questions, allowing students to return to them before the section locks.
* Students cannot access questions in other sections.

### 5. Randomized Question Assignment
Upon starting a session, the backend draws questions randomly from the question bank:
* Advanced Mathematics: 50 random questions
* Basic Mathematics: 20 random questions
* IQ / Analytical Skills: 20 random questions
* English: 30 random questions

The assignment is frozen in the database for the active session.

### 6. Post-Exam Results Screen
Once all sections are completed or submitted:
* A dashboard displays total questions, attempted questions, correct, incorrect, and skipped counts for each section.
* An interactive review section lists all questions, options, the selected response (highlighted green/red), and explanations.
* Includes a built-in FAST Admission Aggregate Calculator allowing students to calculate their aggregate score in real-time by entering their Matric % and FSc/ICS % along with their test score.

---

## Setup and Installation

### Prerequisites
* Node.js (v18 or higher)
* Python 3.8+ (for seeding/scripts)
* A Supabase project instance

### Database Setup
1. Apply the initial schema:
   Locate `supabase/migrations/001_initial_schema.sql` and run it in the SQL Editor of your Supabase dashboard to create the tables, indexes, and row-level security policies.
2. Setup environment variables:
   Copy `.env.example` to `.env` in the root directory and populate it with your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   SUPABASE_PROJECT_ID=your-project-id
   SUPABASE_DB_PASSWORD=your-db-password
   ```

### Seeding the Question Bank
Seed the university configurations, category configurations, and upload the master question bank to the database:
1. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install requests
   ```
2. Run the seeding script:
   ```bash
   python scripts/seed_and_upload.py
   ```

### Running the Frontend
1. Navigate to the frontend project directory:
   ```bash
   cd fast-exam-app
   ```
2. Create the frontend environment file `.env` and configure your credentials:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Build the application for production:
   ```bash
   npm run build
   ```
