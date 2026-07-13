# Workspace Rules — University Entry Test Prep App

## Core Architectural Guardrails

### 1. Scope: Focus on FAST-NUCES, Designed for Multi-University Scalability
* **Current Focus:** The initial build of the database, backend functions, and frontend pages must focus on delivering the mock test experience for **FAST-NUCES**.
* **Scalability Rule:** Never hardcode "fast" or "fast-nuces" in core table designs, frontend components, or API endpoints. All models, routes, and selections must use dynamic parameters (such as `university_id` or `university_slug`).
* **Multi-University Support:** Adding support for a new university (e.g., NUST, UET) in the future must be achievable by purely seeding new rows in the `universities`, `question_categories`, and `university_test_configs` tables, without requiring source code changes.

### 2. Database Schema Consistency
* The schema must preserve the relational mappings defined in `university-entry-test-app-prompt.md`:
  * `questions` must map to `universities(id)` and `question_categories(id)`.
  * Test generation proportions must be driven dynamically by `university_test_configs` joins, never by hardcoded category rules in backend edge functions.

---

## Core App Functionality Rules (Applies to Frontend + Backend + Database)

These rules define how the mock exam works end-to-end and must be respected in every layer of the application.

### 3. Section-Based Independent Timers
* Each section in the FAST mock exam has its own strict, independent countdown timer:
  * **Advanced Mathematics:** 50 minutes
  * **Basic Mathematics:** 20 minutes
  * **IQ / Analytical Skills:** 20 minutes
  * **English:** 30 minutes
* The timer for each section runs independently. Time spent in one section does NOT affect the time available in another section.
* The section timer starts the moment the student enters that section.
* The timer must be persisted server-side (using `section_started_at` timestamps in the database) so that if the student refreshes or closes the tab, the remaining time is correctly recalculated on return.

### 4. Randomized Section Ordering (Per Session)
* The execution order of the four sections is **randomized freshly for every test session**.
* Example: Session A gets [English → IQ → Advanced Math → Basic Math]. Session B gets [Advanced Math → Basic Math → English → IQ].
* The randomized order must be stored in the database at test session creation time (e.g., in a `section_order` JSON column on `test_sessions`) so it is consistent if the student resumes after a refresh.
* The frontend must display the section sequence to the student at all times in the sidebar.

### 5. Section Lockout on Timer Expiry
* When a section's timer reaches `00:00`, that section is **permanently and irrevocably locked**:
  * All currently saved answers in the locked section are preserved as-is.
  * Any unanswered/skipped questions in the locked section are recorded as `null` (not attempted).
  * The backend must enforce the lockout: if a `save-answer` call is received for a locked section, it must be rejected with an error.
  * The frontend must also disable all navigation to locked sections and visually mark them as `[Locked]` in the sidebar.
* After locking, the app automatically transitions the student to the next section in the randomized sequence.
* If all sections are complete (either locked or manually submitted), the exam ends and the results screen is shown.

### 6. Question Skipping & Revisiting (Within Active Section Only)
* Within the **currently active** section, students can freely navigate questions, skip them, and come back.
* A "Skip" action flags the question as unattempted but does NOT lock it — the student can still answer it later within the same section while time remains.
* Skipped questions appear in a separate **"Skipped"** filter view in the question grid sidebar, allowing the student to jump directly to them.
* Once a section is locked (timer expired or section submitted), skipped questions in that section are permanently recorded as unanswered (`null`).
* Students **cannot** navigate to questions in a different section (past or future) from the active question view.

### 7. Randomized Question Assignment Per Session
* On every new test session, questions are drawn **randomly** from the question bank:
  * Advanced Mathematics: 50 random questions drawn from the math pool.
  * Basic Mathematics: 20 random questions drawn from the basic math pool.
  * IQ / Analytical Skills: 20 random questions drawn from the IQ pool.
  * English: 30 random questions drawn from the English pool.
* Questions are NOT required to be unique across sessions — the same question may appear in multiple attempts. The randomness ensures variety without guaranteeing exclusivity.
* The question selection must be done server-side at session creation time and stored in `test_session_questions` so the set is frozen for that session.

### 8. Results Screen (Post-Exam)
* After the exam ends (all sections complete or student manually submits), the student is shown a dedicated Results screen.
* The Results screen must display, **for each section individually**:
  * Total questions in the section (e.g., 50).
  * Total questions **attempted** (answered, not skipped) by the student.
  * Total questions answered **correctly**.
  * Total questions answered **incorrectly**.
  * Total questions **skipped/unanswered**.
* The Results screen must also show an overall total score and percentage across all sections combined.
* A detailed question-by-question review must be available, showing: the question text, all 4 options, the student's selected answer (highlighted red if wrong, green if correct), and the correct answer.
* The Results screen must include a **FAST Aggregate Calculator** widget where the student can enter their Matric % and FSc/ICS % and see their computed FAST admission aggregate in real time based on their mock test score.
