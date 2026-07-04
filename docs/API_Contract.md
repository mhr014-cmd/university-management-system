# API Contract
## University Management System (ICT Education) — REST API v1

**Source inputs:** `docs/product_proposal.pdf` §6, `docs/Requirement_Analysis.md`, `docs/System_Architecture.md`, `docs/Database_Design.md`, `docs/Implementation_Roadmap.md`
**Base URL:** `/api/v1`
**Format:** All requests/responses are JSON. All protected endpoints require `Authorization: Bearer <access_token>` unless marked Public.
**Scope:** This document is documentation only — no FastAPI route code, no Pydantic models, no application code of any kind. JSON blocks below describe the *shape* of data, not implementation.

**Common response envelope (all endpoints):**
- Success: the resource or list is returned directly as JSON (object or array).
- Error: `{ "error": { "code": "string", "message": "string", "details": [ ... ] } }` per `System_Architecture.md` §9.

**Common error codes used throughout this document:**
| Status | Meaning | When |
|---|---|---|
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Missing, invalid, or expired token |
| 403 | Forbidden | Valid token, but role/ownership check fails |
| 404 | Not Found | Resource does not exist, or hidden intentionally (see `System_Architecture.md` §6) |
| 409 | Conflict | Business rule violation (e.g., duplicate, invalid state transition) |
| 422 | Unprocessable Entity | Schema/field-level validation failure |
| 500 | Internal Server Error | Unhandled server fault |

---

## 1. Authentication

### 1.1 `POST /auth/login`

- **Purpose:** Authenticate a user with email/password and issue tokens. (FR-001)
- **Authentication Required:** No (Public)
- **User Roles:** All (unauthenticated)
- **Request Body:**
```json
{
  "email": "string (valid email)",
  "password": "string"
}
```
- **Response Body (200):**
```json
{
  "access_token": "string (JWT)",
  "refresh_token": "string (JWT)",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "string",
    "role": "student | teacher | parent | admin"
  }
}
```
- **Validation:** VR-001 — email must be syntactically valid, password non-empty.
- **Possible Errors:** Invalid email format (422); missing fields (422); incorrect credentials (401); account deactivated (`user.is_active = false`) (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `user`.
- **Business Rules:** Deactivated accounts (BR-006) must fail login even with correct credentials.

### 1.2 `POST /auth/refresh`

- **Purpose:** Exchange a valid refresh token for a new access token. (FR-002)
- **Authentication Required:** No bearer access token required; a valid refresh token is required in the request body/cookie.
- **User Roles:** All (previously authenticated)
- **Request Body:**
```json
{
  "refresh_token": "string (JWT)"
}
```
- **Response Body (200):**
```json
{
  "access_token": "string (JWT)",
  "refresh_token": "string (JWT, rotated)",
  "token_type": "bearer"
}
```
- **Validation:** Refresh token must be well-formed and not expired/revoked.
- **Possible Errors:** Refresh token missing (422); refresh token invalid, expired, or revoked (401).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `user` — re-verifies `is_active`, and compares the presented token's `jti` claim against `user.current_refresh_token_jti` (per `Database_Design.md` §6.1 Milestone 2 design note) to detect reuse of an already-rotated or logged-out token.
- **Business Rules:** Refresh tokens are rotated on use (NFR-004) — `user.current_refresh_token_jti` is updated to the new token's `jti` and `refresh_token_expires_at` extended; the old `jti` no longer matches and is rejected if presented again.

### 1.3 `POST /auth/logout`

- **Purpose:** Invalidate the current session's refresh token. (FR-003)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:** none (or `{ "refresh_token": "string" }` if the refresh token must be explicitly revoked)
- **Response Body (204):** no content
- **Validation:** none beyond authentication.
- **Possible Errors:** Missing/invalid access token (401).
- **Status Codes:** 204 No Content, 401 Unauthorized.
- **Database Tables Used:** `user` — clears `current_refresh_token_jti` and `refresh_token_expires_at` (per `Database_Design.md` §6.1 Milestone 2 design note), so the refresh token the client discards is also rejected server-side if it's ever presented again.
- **Business Rules:** none beyond immediate session invalidation.

### 1.4 `PUT /auth/password`

- **Purpose:** Change the authenticated user's own password. (FR-004)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```
- **Response Body (200):**
```json
{ "message": "Password updated successfully" }
```
- **Validation:** VR-002 — `new_password` must differ from `current_password` and meet minimum complexity (policy TBD — see `Requirement_Analysis.md` §14 item 13).
- **Possible Errors:** `current_password` incorrect (401 or 403 — reject re-auth); `new_password` fails complexity rule (422); `new_password` equals `current_password` (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `user`.
- **Business Rules:** none beyond VR-002.

---

## 2. Users & Profiles

### 2.1 `GET /users/me`

- **Purpose:** Retrieve the authenticated user's own profile, merged with role-specific fields. (FR-006)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:** none
- **Response Body (200):**
```json
{
  "id": "uuid",
  "email": "string",
  "role": "student | teacher | parent | admin",
  "profile": {
    "first_name": "string",
    "last_name": "string",
    "profile_photo_url": "string | null",
    "department_id": "uuid | null"
  }
}
```
- **Validation:** none beyond authentication.
- **Possible Errors:** Missing/invalid token (401).
- **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `user`, plus the role-specific table (`student`, `teacher`, `parent`, or `admin`).
- **Business Rules:** none — always scoped to the caller's own `user_id` (NFR-002).

### 2.2 `PUT /users/me`

- **Purpose:** Update the authenticated user's own profile. (FR-007)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:**
```json
{
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "profile_photo_url": "string (optional)"
}
```
- **Response Body (200):** same shape as `GET /users/me`.
- **Validation:** VR-009 — role, `is_active`, `department_id`, and other Admin-controlled fields must not be accepted/modified through this endpoint.
- **Possible Errors:** Attempt to set a restricted field (422); invalid photo URL/format (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `user`, role-specific table (`student`/`teacher`/`parent`/`admin`).
- **Business Rules:** VR-009.

### 2.3 `GET /users/students`

- **Purpose:** List all students. (FR-009)
- **Authentication Required:** Yes
- **User Roles:** Admin, Teacher
- **Request Body:** none. Query params: `department_id` (optional filter), `page`, `page_size` (pagination, per `CLAUDE.md` §11 performance guideline).
- **Response Body (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "department_id": "uuid",
      "is_active": "boolean",
      "created_at": "timestamp"
    }
  ],
  "total": "integer",
  "page": "integer",
  "page_size": "integer"
}
```
- **Validation:** none beyond query param type validation.
- **Possible Errors:** Caller is not Admin/Teacher (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden.
- **Database Tables Used:** `student`, `user`, `department`.
- **Business Rules:** none.
- **Note (Milestone 10, Finding D):** `created_at` (sourced from `user.created_at`, which already existed) is an additive field added to support the Admin Dashboard's Recent User Signups widget (`UI_Wireframes.md`) — no business logic or schema change, no new endpoint. Also present on every other student/teacher response in this section (2.4–2.10) that shares this same object shape.

### 2.4 `POST /users/students`

- **Purpose:** Create a new student account. (FR-010)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "email": "string (valid, unique)",
  "password": "string (initial password, or omitted if invite-based provisioning is used)",
  "first_name": "string",
  "last_name": "string",
  "department_id": "uuid",
  "enrollment_date": "date"
}
```
- **Response Body (201):** the created student record, same shape as a row from `GET /users/students`.
- **Validation:** VR-001 (email format); `email` must be unique (`user.email` uniqueness constraint); `department_id` must reference an existing `department`.
- **Possible Errors:** Duplicate email (409); invalid/nonexistent `department_id` (422); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `user`, `student`.
- **Business Rules:** none beyond uniqueness.

### 2.5 `GET /users/students/{id}`

- **Purpose:** Retrieve a single student's record. (FR-011)
- **Authentication Required:** Yes
- **User Roles:** Admin, Teacher
- **Request Body:** none.
- **Response Body (200):** single student object, same shape as a row from `GET /users/students`.
- **Validation:** `{id}` must be a valid UUID.
- **Possible Errors:** Student not found (404); caller is not Admin/Teacher (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `student`, `user`.
- **Business Rules:** none.

### 2.6 `PUT /users/students/{id}`

- **Purpose:** Update a student's record. (FR-012)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "department_id": "uuid (optional)",
  "is_active": "boolean (optional)"
}
```
- **Response Body (200):** updated student object.
- **Validation:** `department_id` (if provided) must reference an existing `department`.
- **Possible Errors:** Student not found (404); invalid `department_id` (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
- **Database Tables Used:** `student`, `user`.
- **Business Rules:** none beyond referential validity.

### 2.7 `DELETE /users/students/{id}`

- **Purpose:** Deactivate a student account (soft delete). (FR-013)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none.
- **Response Body (200):**
```json
{ "id": "uuid", "is_active": false }
```
- **Validation:** `{id}` must reference an existing student.
- **Possible Errors:** Student not found (404); caller is not Admin (403); student already deactivated (idempotent — may return 200 or 409 depending on chosen semantics, must be decided consistently at implementation).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `student`, `user`.
- **Business Rules:** BR-006 — this is a soft deactivation (`user.is_active = false`), never a row deletion; historical Attendance/Result/Payment records must remain intact.

### 2.8 `GET /users/teachers`

- **Purpose:** List all teachers. (FR-014)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `department_id` (optional), `page`, `page_size`.
- **Response Body (200):** paginated list, same envelope shape as `GET /users/students`, teacher fields.
- **Validation:** none beyond query param types.
- **Possible Errors:** Caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden.
- **Database Tables Used:** `teacher`, `user`, `department`.
- **Business Rules:** none.

### 2.9 `POST /users/teachers`

- **Purpose:** Create a new teacher account. (FR-015)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "email": "string (valid, unique)",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "department_id": "uuid",
  "hire_date": "date (optional)"
}
```
- **Response Body (201):** created teacher record.
- **Validation:** VR-001; `email` uniqueness; `department_id` referential validity.
- **Possible Errors:** Duplicate email (409); invalid `department_id` (422); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `user`, `teacher`.
- **Business Rules:** none beyond uniqueness.

### 2.10 `PUT /users/teachers/{id}`

- **Purpose:** Update a teacher's record. (FR-016)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "department_id": "uuid (optional)",
  "is_active": "boolean (optional)"
}
```
- **Response Body (200):** updated teacher object.
- **Validation:** `department_id` referential validity.
- **Possible Errors:** Teacher not found (404); invalid `department_id` (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
- **Database Tables Used:** `teacher`, `user`.
- **Business Rules:** none beyond referential validity.

---

## 3. Exams & Grading

### 3.1 `GET /exams`

- **Purpose:** List exams filtered by the caller's role/context. (FR-017)
- **Authentication Required:** Yes
- **User Roles:** All roles (Student sees exams for enrolled `class_session`s; Teacher sees exams they created; Admin sees all)
- **Request Body:** none. Query params: `class_session_id` (optional), `status` (optional filter), `page`, `page_size`.
- **Response Body (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "class_session_id": "uuid",
      "exam_type": "mcq | written | practical_coding | mixed",
      "time_limit_minutes": "integer",
      "status": "draft | scheduled | open | closed | published",
      "scheduled_at": "timestamp | null"
    }
  ],
  "total": "integer", "page": "integer", "page_size": "integer"
}
```
- **Validation:** none beyond query param types.
- **Possible Errors:** none role-specific beyond standard auth failures.
- **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `exam`, `class_session`.
- **Business Rules:** result set is scoped by role (Student: enrolled classes only; Teacher: own-created exams; per NFR-002).

### 3.2 `POST /exams`

- **Purpose:** Create a new exam with questions, assigned to a class. (FR-018)
- **Authentication Required:** Yes
- **User Roles:** Teacher
- **Request Body:**
```json
{
  "class_session_id": "uuid",
  "title": "string",
  "exam_type": "mcq | written | practical_coding | mixed",
  "time_limit_minutes": "integer (> 0)",
  "questions": [
    {
      "question_text": "string",
      "question_type": "mcq | short_answer | descriptive | coding",
      "marks": "number (> 0)",
      "hint": "string (optional)",
      "order_index": "integer",
      "options": [
        { "option_text": "string", "is_correct": "boolean" }
      ]
    }
  ]
}
```
- **Response Body (201):** created exam with nested questions/options, `status: "draft"`.
- **Validation:** VR-003 (marks > 0 per question), VR-004 (time_limit_minutes > 0); `class_session_id` must reference an existing class session taught by the caller.
- **Possible Errors:** Invalid `class_session_id` or not owned by caller (403/422); question marks <= 0 (422); time limit <= 0 (422); MCQ question with no `is_correct = true` option (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `exam`, `question`, `question_option`, `class_session`.
- **Business Rules:** exam is created in `draft` status.

### 3.3 `GET /exams/{id}`

- **Purpose:** View exam details and questions. (FR-019)
- **Authentication Required:** Yes
- **User Roles:** All roles (Student view excludes `is_correct` flags and any grading data until published, per BR-001)
- **Request Body:** none.
- **Response Body (200):** exam object with nested questions (and options for MCQ), shape mirrors `POST /exams` response minus role-restricted fields for Students.
- **Validation:** `{id}` valid UUID.
- **Possible Errors:** Exam not found or not accessible to caller (404); Student requesting an exam outside their enrollment (404, per ownership-hiding convention in `System_Architecture.md` §6).
- **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found.
- **Database Tables Used:** `exam`, `question`, `question_option`.
- **Business Rules:** BR-001 — correct-answer/grading data hidden from Students until the exam's results are published.

### 3.4 `PUT /exams/{id}`

- **Purpose:** Update an exam (questions, marks, time limit). (FR-020)
- **Authentication Required:** Yes
- **User Roles:** Teacher (must be the exam's creator)
- **Request Body:** same shape as `POST /exams` (partial updates allowed for top-level fields; question list replacement semantics to be defined at implementation).
- **Response Body (200):** updated exam object.
- **Validation:** VR-003, VR-004; exam must not be in `published` status (see BR-003 — update restriction likely mirrors delete restriction and must be confirmed at implementation).
- **Possible Errors:** Exam not found (404); caller is not the creating Teacher (403); exam already published (409); invalid marks/time limit (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `exam`, `question`, `question_option`.
- **Business Rules:** VR-003, VR-004; update restricted once published (extension of BR-003).

### 3.5 `DELETE /exams/{id}`

- **Purpose:** Delete an unpublished exam. (FR-021)
- **Authentication Required:** Yes
- **User Roles:** Teacher, Admin
- **Request Body:** none.
- **Response Body (204):** no content.
- **Validation:** exam must be in a non-`published` status.
- **Possible Errors:** Exam not found (404); exam is `published` (409, per BR-003); caller is neither the creating Teacher nor Admin (403).
- **Status Codes:** 204 No Content, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `exam`, `question`, `question_option` (cascade delete on unpublished draft children, per `Database_Design.md` §10).
- **Business Rules:** BR-003.

### 3.6 `POST /exams/{id}/start` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** Student begins an exam attempt, establishing the server-recorded start time VR-004's time-limit enforcement depends on. Added during the Milestone 6 pre-implementation review — `UI_Wireframes.md` §5 (Exam Room) describes zero server round-trips during the exam except the final `POST /exams/{id}/submit` (answers autosave client-side only), but nothing anywhere created the `exam_submission` row or recorded `started_at` before that final call. Without a server-side start time recorded independently of the client, VR-004 cannot be genuinely enforced — a student could submit any elapsed-time claim. The frontend calls this once, when the Student enters the Exam Room.
- **Authentication Required:** Yes
- **User Roles:** Student
- **Request Body:** none.
- **Response Body (200 or 201):**
```json
{
  "submission_id": "uuid",
  "exam_id": "uuid",
  "status": "in_progress",
  "started_at": "timestamp"
}
```
- 201 if a new `exam_submission` was created; 200 if an in-progress submission already existed for this student and exam, in which case the *existing* row (and its original `started_at`) is returned unchanged — this endpoint is idempotent, not a re-start.
- **Validation:** exam must exist and be in `open` status; caller (Student) must be enrolled in the exam's `class_session`; if a submission for this student/exam already has `status = submitted` or `status = graded`, starting again is rejected (one attempt per student per exam, per `exam_submission`'s own uniqueness constraint).
- **Possible Errors:** Exam not found (404); exam not `open` (409); caller not enrolled in the exam's class (403); an already-submitted/graded attempt exists for this student and exam (409).
- **Status Codes:** 200 OK, 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `exam_submission`, `exam`, `enrollment`.
- **Business Rules:** `started_at` is set from the server clock only (`datetime.now(timezone.utc)`), never a client-supplied value, and is immutable once the row is created — no endpoint ever updates it. `POST /exams/{id}/submit` (3.7 below) reads this same stored value to compute elapsed time; it never accepts or trusts a client-provided start time.
- **Note:** Classified **Derived** (unavoidable prerequisite for genuine server-side VR-004 enforcement), not Design Enhancement — confirmed with the user during the Milestone 6 pre-implementation review. See `Proposal_vs_Engineering_Additions.md`.

### 3.7 `POST /exams/{id}/submit`

- **Purpose:** Student submits answers to an exam. (FR-022)
- **Authentication Required:** Yes
- **User Roles:** Student
- **Request Body:**
```json
{
  "answers": [
    {
      "question_id": "uuid",
      "answer_text": "string (optional)",
      "selected_option_id": "uuid (optional, MCQ only)"
    }
  ]
}
```
- **Response Body (201):**
```json
{
  "submission_id": "uuid",
  "exam_id": "uuid",
  "status": "submitted",
  "submitted_at": "timestamp"
}
```
- **Validation:** an `in_progress` `exam_submission` must already exist for this student/exam (created via `POST /exams/{id}/start`, 3.6 above) — submitting without first starting is rejected; exam must be in `open` status; the elapsed time between the stored server-side `started_at` and the current server time must not exceed `time_limit_minutes` (VR-004 — computed entirely server-side, never from a client-supplied timestamp); one submission per student per exam (`exam_submission` uniqueness); one answer per question (`answer` uniqueness).
- **Possible Errors:** No `in_progress` submission exists to submit against (404 or 409 — must be decided consistently at implementation); exam not open (409); time limit exceeded (409); duplicate submission (409); exam/question not found (404); caller not enrolled in the exam's class (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `exam_submission`, `answer`, `exam`.
- **Business Rules:** VR-004 (time limit enforcement, using the stored server-side `started_at` from 3.6 — never a client timestamp); one submission per student per exam.

### 3.8 `GET /exams/{id}/submissions/{submission_id}` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** Retrieve a single student's submission in full detail — the exam's questions in order, each with the student's submitted answer and any existing grading already recorded for it — so a Teacher can actually grade it. (Supports FR-023.) Added during Milestone 6 frontend implementation: `POST /exams/{id}/grade` (3.9 below) requires `answer_id` values but nothing returned an `answer_id` alongside the student's actual answer text/selection, and `GET /exams/{id}/results` (3.10 below) deliberately stays aggregate-only (reporting, not grading) — see `Proposal_vs_Engineering_Additions.md` for why the two responsibilities are not merged into one endpoint.
- **Authentication Required:** Yes
- **User Roles:** Teacher (must be the exam's creator), Admin
- **Request Body:** none.
- **Response Body (200):**
```json
{
  "submission_id": "uuid",
  "exam_id": "uuid",
  "student_id": "uuid",
  "status": "submitted | graded",
  "questions": [
    {
      "question_id": "uuid",
      "question_text": "string",
      "question_type": "mcq | short_answer | descriptive | coding",
      "marks": "number",
      "order_index": "integer",
      "answer_id": "uuid",
      "answer_text": "string | null",
      "selected_option_id": "uuid | null",
      "awarded_marks": "number | null",
      "feedback": "string | null"
    }
  ]
}
```
- **Validation:** `{id}` and `{submission_id}` valid UUIDs; the submission must belong to the specified exam.
- **Possible Errors:** Exam not found (404); submission not found or does not belong to this exam (404); caller is a Teacher who did not create this exam (403); caller is neither Teacher nor Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `exam`, `question`, `exam_submission`, `answer`, `question_grade`.
- **Business Rules:** none beyond the ownership check above; questions are returned in `order_index` order.
- **Note:** Classified **Derived** — required to make the documented Grading Interface (`UI_Wireframes.md` §14) functional at all, not a new feature beyond what §14 already describes. Confirmed with the user during Milestone 6 frontend implementation. See `Proposal_vs_Engineering_Additions.md`.

### 3.9 `POST /exams/{id}/grade`

- **Purpose:** Teacher grades a submitted exam. (FR-023)
- **Authentication Required:** Yes
- **User Roles:** Teacher (must be the exam's creator)
- **Request Body:**
```json
{
  "submission_id": "uuid",
  "grades": [
    {
      "answer_id": "uuid",
      "awarded_marks": "number (>= 0)",
      "feedback": "string (optional)"
    }
  ]
}
```
- **Response Body (200):**
```json
{
  "submission_id": "uuid",
  "status": "graded",
  "total_awarded_marks": "number"
}
```
- **Validation:** VR-006 — `awarded_marks` for each answer must not exceed that question's defined `marks`.
- **Possible Errors:** Submission not found (404); `awarded_marks` exceeds question's max marks (422); caller is not the exam's creating Teacher (403); submission already graded (409, if re-grading is disallowed — policy TBD).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
- **Database Tables Used:** `exam_submission`, `answer`, `question_grade`, `question`.
- **Business Rules:** VR-006.

### 3.10 `GET /exams/{id}/results`

- **Purpose:** Retrieve all graded results for a given exam. (FR-024)
- **Authentication Required:** Yes
- **User Roles:** Teacher, Admin
- **Request Body:** none.
- **Response Body (200):**
```json
{
  "exam_id": "uuid",
  "submissions": [
    {
      "student_id": "uuid",
      "submission_id": "uuid",
      "total_awarded_marks": "number",
      "status": "graded"
    }
  ]
}
```
- **Validation:** `{id}` valid UUID.
- **Possible Errors:** Exam not found (404); caller is not Teacher/Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `exam_submission`, `question_grade`, `answer`.
- **Business Rules:** none.

---

## 4. Attendance

### 4.1 `GET /attendance/me`

- **Purpose:** Student's own attendance summary, filterable by subject/date, with current percentage. (FR-026)
- **Authentication Required:** Yes
- **User Roles:** Student
- **Request Body:** none. Query params: `class_session_id` (optional), `date_from`, `date_to` (optional).
- **Response Body (200):**
```json
{
  "overall_percentage": "number",
  "low_attendance_warning": "boolean",
  "by_class_session": [
    {
      "class_session_id": "uuid",
      "course_name": "string",
      "percentage": "number",
      "low_attendance_warning": "boolean",
      "records": [
        { "date": "date", "status": "present | absent | late | excused" }
      ]
    }
  ]
}
```
- **Validation:** date range params must be valid dates, `date_from <= date_to`.
- **Possible Errors:** invalid date range (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `attendance_record`, `class_session`, `enrollment`.
- **Business Rules:** percentage computed on demand, never cached (NFR-016). `low_attendance_warning` is `true` when the corresponding percentage is below 80% (BR-008/FR-031, threshold resolved during the Milestone 5 pre-implementation review — see `Requirement_Analysis.md` §14 item 4); this is a computed indicator only, not a dispatched notification (Milestone 9 scope).

### 4.2 `POST /attendance`

- **Purpose:** Teacher marks attendance for a class and date. (FR-027)
- **Authentication Required:** Yes
- **User Roles:** Teacher
- **Request Body:**
```json
{
  "class_session_id": "uuid",
  "attendance_date": "date",
  "records": [
    { "student_id": "uuid", "status": "present | absent | late | excused" }
  ]
}
```
- **Response Body (201):** created attendance records for the given class/date.
- **Validation:** VR-005 — class session must exist, date must be valid (not arbitrarily future-dated beyond current session), no duplicate record for the same student/class_session/date.
- **Possible Errors:** Duplicate attendance for a student/date (409); invalid `class_session_id` (404); student not enrolled in the class (422); caller is not the class's assigned Teacher (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `attendance_record`, `class_session`, `enrollment`, `notification` (Milestone 9 dispatch).
- **Business Rules:** VR-005; triggers low-attendance warning evaluation (FR-031/BR-008, threshold 80% — resolved during the Milestone 5 pre-implementation review, see `Requirement_Analysis.md` §14 item 4). Evaluation surfaces the crossed-threshold state in `GET /attendance/me`'s response. **Notification dispatch (resolved during the Milestone 9 pre-implementation review, confirmed with the user):** an `attendance_warning` notification is created only on a genuine threshold *crossing* — the student's overall percentage was `>= 80%` immediately before this record was written and is `< 80%` immediately after. Marking additional records while the student remains below 80% does not repeat the notification (Domain Rule 5); if the student later recovers to `>= 80%` and falls below again, a new notification is generated for that new crossing.

### 4.3 `GET /attendance/{classId}`

- **Purpose:** Retrieve attendance for a specific class. (FR-028)
- **Authentication Required:** Yes
- **User Roles:** Teacher, Admin (also used, parent-scoped, to satisfy FR-032 per `Requirement_Traceability_Matrix.md`)
- **Request Body:** none. Query params: `date_from`, `date_to` (optional), `student_id` (optional).
- **Response Body (200):**
```json
{
  "class_session_id": "uuid",
  "records": [
    { "id": "uuid", "student_id": "uuid", "date": "date", "status": "present | absent | late | excused" }
  ]
}
```
- **Note:** `id` added during Milestone 5 implementation, beyond this document's original shape — `PUT /attendance/{id}` (the correction workflow, FR-029) needs the record's own id, which `student_id`/`date`/`status` alone can't resolve. Found while implementing the Teacher: Attendance Marker page's correction mode; fixed here in the same change per `CLAUDE.md` Section 9.
- **Validation:** `{classId}` valid UUID.
- **Possible Errors:** Class not found (404); caller is not Teacher of that class/Admin, and not a Parent linked to the requested `student_id` (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `attendance_record`, `class_session`, `parent_student_link` (for Parent-scoped access checks).
- **Business Rules:** BR-007 for Parent access.

### 4.4 `PUT /attendance/{id}`

- **Purpose:** Correct an existing attendance record. (FR-029)
- **Authentication Required:** Yes
- **User Roles:** Teacher, Admin
- **Request Body:**
```json
{ "status": "present | absent | late | excused" }
```
- **Response Body (200):** updated attendance record.
- **Validation:** record must exist; `status` must be one of the allowed enum values.
- **Possible Errors:** Record not found (404); invalid status value (422); caller is not the marking Teacher/Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
- **Database Tables Used:** `attendance_record`.
- **Business Rules:** none beyond VR-005 (still one record per student/class/date — correction, not duplication).

### 4.5 `GET /attendance/reports`

- **Purpose:** Generate attendance reports by department or semester. (FR-030)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `department_id` (optional), `semester_id` (optional).
- **Response Body (200):**
```json
{
  "scope": { "department_id": "uuid | null", "semester_id": "uuid | null" },
  "summary": [
    { "student_id": "uuid", "percentage": "number" }
  ]
}
```
- **Validation:** `department_id`/`semester_id` if provided must reference existing rows.
- **Possible Errors:** invalid `department_id`/`semester_id` (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `attendance_record`, `department`, `semester`, `class_session`.
- **Business Rules:** none.

---

## 5. Results & Transcripts

### 5.1 `GET /results/me`

- **Purpose:** Student's own results across all semesters, incl. GPA. (FR-033) Also used, parent-scoped, for FR-037.
- **Authentication Required:** Yes
- **User Roles:** Student (own record only), Parent (linked child only, via `parent_student_link`)
- **Request Body:** none. Query params: `semester_id` (optional); `student_id` (**required for Parent callers** — resolved during the Milestone 7 pre-implementation review, same pattern as `GET /attendance/{classId}`'s Parent scoping in Milestone 5: a Parent must specify which linked child, verified against `parent_student_link` server-side, per BR-007/NFR-003; ignored/not required for a Student caller, who always sees their own record).
- **Response Body (200):**
```json
{
  "student_id": "uuid",
  "semesters": [
    {
      "semester_id": "uuid",
      "semester_name": "string",
      "gpa": "number",
      "courses": [
        { "course_id": "uuid", "course_name": "string", "grade_letter": "string", "grade_point": "number" }
      ]
    }
  ]
}
```
- `gpa` is a **credit-hour-weighted average** of `grade_point` across the semester's `published` results (`sum(grade_point * course.credit_hours) / sum(course.credit_hours)`) — resolves `Requirement_Analysis.md` §14 item 6 per that document's own A-004 assumption ("a conventional university GPA scheme," credit-hour-weighted). Not hard-coded elsewhere; this is the single implementation of the formula.
- `student_id` (added during Milestone 7 frontend implementation, same class of fix as Milestone 5's `GET /attendance/{classId}` `id`-field addition): the resolved target student — the caller's own id for a Student, the queried child's id for a Parent. Added because `GET /results/{studentId}/transcript` needs a `student_id` and nothing else returns a Student caller's own `student.id` anywhere.
- **Validation:** `semester_id` if provided must reference an existing semester; `student_id` required and must reference a linked student for a Parent caller (403 otherwise, per the ownership-hiding convention — no confirmation of the student's existence is leaked to an unlinked Parent).
- **Possible Errors:** invalid `semester_id` (422); Parent caller missing/unlinked `student_id` (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `semester`, `course`.
- **Business Rules:** BR-001/BR-002 — only `published` results are returned to Student/Parent callers.

### 5.2 `POST /results/{examId}/submit`

- **Purpose:** Teacher submits a course's final results for admin approval, gated on one exam of that course being fully graded and published. (FR-034)
- **Authentication Required:** Yes
- **User Roles:** Teacher (must be the exam's creator)
- **Request Body:**
```json
{
  "results": [
    { "student_id": "uuid", "grade_letter": "string", "grade_point": "number" }
  ]
}
```
- **Response Body (201):**
```json
{ "exam_id": "uuid", "status": "submitted", "submitted_at": "timestamp" }
```
- **Validation:** `exam.status` must be `published` (Milestone 7 mandatory Domain Rule 4 — resolved during the Milestone 7 pre-implementation review: `exam.status = published` is the same server-side transition the Milestone 6 Grading Interface's own "Publish Exam" action already performs, so this rule requires no new exam-side mechanism); the exam must be fully graded (every `exam_submission` for it has `question_grade` entries for all its answers — Domain Rule 5); for every `student_id` in the payload, that student must have a `submitted`/`graded` `exam_submission` for this exam with `question_grade` entries (Domain Rule 6 — a Teacher cannot submit a result for a student never graded on this exam); `student_id` must have a valid `enrollment` for the exam's `class_session` (Domain Rule 2).
- **Resubmission policy** (resolved during the Milestone 7 pre-implementation review, confirmed with the user): a `result` row already exists for a given (student, course, semester) if that student has a prior result for this exam's course/semester from any earlier exam. If that row's status is `submitted` or `published`, this call is rejected with 409 for that student. If that row's status is `rejected`, it is updated in place instead of erroring (new `exam_id`, new grade values, status reset to `submitted`) — see `Database_Design.md` §6.21's Milestone 7 design note.
- **Possible Errors:** Exam not published (409); exam not fully graded (409); a target student was never graded on this exam (422); exam not found (404); caller is not the exam's creating Teacher (403); an existing `submitted`/`published` result already exists for a target student's course/semester (409).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `exam`, `exam_submission`, `question_grade`, `enrollment`.
- **Business Rules:** BR-002 — enters `submitted` status, not visible to Student/Parent yet. Per Milestone 7's Domain Rule 9, this endpoint only *reads* `exam`/`exam_submission`/`answer`/`question_grade` — it never modifies them.

### 5.3 `GET /results/pending` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** Admin retrieves the queue of results awaiting review, grouped by the exam/course submission batch, each with its per-student grade entries — the data the Admin: Result Approval page (`UI_Wireframes.md` §11) needs to render its queue table and expandable per-exam review panel. Added during Milestone 7 implementation: none of this milestone's other three endpoints can list or retrieve pending results at all, and `GET /results/reports` (§9.1) is a different, aggregate-only, published-results-only reporting endpoint out of Milestone 7's scope.
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `status` (optional, default `submitted`; also accepts `published`/`rejected` per the wireframe's Status filter).
- **Response Body (200):**
```json
{
  "items": [
    {
      "exam_id": "uuid | null",
      "exam_title": "string | null",
      "course_id": "uuid",
      "course_name": "string",
      "submitted_by_teacher_id": "uuid",
      "submitted_by_teacher_name": "string",
      "submitted_at": "timestamp",
      "status": "submitted | published | rejected",
      "results": [
        { "result_id": "uuid", "student_id": "uuid", "student_name": "string", "grade_letter": "string | null", "grade_point": "number | null" }
      ]
    }
  ]
}
```
- Rows are grouped by `(exam_id, course_id, submitted_by_teacher_id, submitted_at)` — the same batch a single `POST /results/{examId}/submit` call created or last updated.
- **Validation:** `status` if provided must be one of `submitted`/`published`/`rejected`.
- **Possible Errors:** invalid `status` value (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `exam`, `course`, `teacher`, `student`.
- **Business Rules:** none beyond the Admin-only RBAC check above.
- **Note:** Classified **Derived** — required to make the documented Admin: Result Approval queue functional at all, not a new feature beyond what `UI_Wireframes.md` §11 already describes. Confirmed with the user during Milestone 7 implementation. See `Proposal_vs_Engineering_Additions.md`.

### 5.4 `POST /results/{id}/approve`

- **Purpose:** Admin approves and publishes submitted results. (FR-035)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{ "decision": "approve | reject", "comment": "string (required if reject)" }
```
- **Response Body (200):**
```json
{ "id": "uuid", "status": "published | rejected", "approved_at": "timestamp | null" }
```
- **Validation:** result must currently be in `submitted` status; `comment` is **required** when `decision = reject` (resolved during the Milestone 7 pre-implementation review from `UI_Wireframes.md` §11's own wireframe/Validation text, which already shows and requires the comment field for reject — closing this contract's own previously-flagged "policy TBD").
- **Possible Errors:** Result not found (404); result not in `submitted` status (409); caller is not Admin (403); `reject` decision missing a comment (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `result`.
- **Business Rules:** BR-002 — enforces the `submitted → published` (or `→ rejected`) state transition. Publication triggers a `result_published` notification to the affected Student (FR-052) once the transition commits — implemented in Milestone 9. **Note (resolved during the Milestone 9 pre-implementation review, confirmed with the user):** this is also the sole notification for the exam-grading pipeline — Milestone 6's `exam.status = published` transition (revealing marks/correct answers) is a UI-visibility change only, not a separate documented notification event; no new notification type was added for it.

### 5.5 `GET /results/{studentId}/transcript`

- **Purpose:** Download an official PDF transcript with university seal. (FR-036)
- **Authentication Required:** Yes
- **User Roles:** Student (own record only), Admin
- **Request Body:** none.
- **Response Body (200):** binary PDF stream, `Content-Type: application/pdf`.
- **Validation:** `{studentId}` must reference an existing, active student; only `published` results are included.
- **Possible Errors:** Student not found (404); caller is a Student requesting another student's transcript (403); no published results available yet — resolved during the Milestone 7 pre-implementation review: returns **200 with an empty-results PDF** (a valid, generated transcript document stating no published results exist yet), not a 409, since a transcript is a document about a student's current state, and "no results yet" is a legitimate, displayable state rather than an error condition.
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `result`, `student`, `semester`, `course`.
- **Business Rules:** BR-002 — only published results appear on the transcript.

---

## 6. Fees (Optional Module)

### 6.1 `GET /fees/me`

- **Purpose:** Student or Parent retrieves fee status and payment history. (FR-038)
- **Authentication Required:** Yes
- **User Roles:** Student, Parent
- **Request Body:** none. Query params: `semester_id` (optional); `student_id` (**required for Parent callers**, ignored/not required for a Student caller who always sees their own record — resolved during the Milestone 8 pre-implementation review, same pattern as Milestone 7's `GET /results/me`).
- **Response Body (200):**
```json
{
  "student_id": "uuid",
  "outstanding_balance": "number",
  "invoices": [
    { "invoice_id": "uuid", "amount": "number", "status": "unpaid | partially_paid | paid | overdue", "due_date": "date" }
  ],
  "payments": [
    { "payment_id": "uuid", "amount": "number", "payment_date": "timestamp" }
  ]
}
```
- `student_id` (added proactively, same class of field as Milestone 7's `GET /results/me` fix) is the resolved target student, so the frontend can construct `GET /fees/invoices/{id}`/other student-scoped URLs without a separate lookup.
- **Validation:** none beyond authentication; Parent callers are scoped to their linked child/children via a required `student_id` query param (same pattern as `GET /results/me` in Milestone 7 — verified against `parent_student_link` server-side).
- `invoices[].status` reflects the derived `overdue` value at read time (`unpaid`/`partially_paid` + `due_date` in the past), never a stale stored value — see `Database_Design.md` §6.25's design note.
- **Possible Errors:** Parent caller missing/unlinked `student_id` (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden.
- **Database Tables Used:** `fee_structure`, `payment`, `invoice`, `parent_student_link` (Parent scoping).
- **Business Rules:** BR-007 (Parent scoping); NFR-016 (computed on demand).

### 6.2 `POST /fees`

- **Purpose:** Admin defines a fee structure per semester/department. (FR-039)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "department_id": "uuid (optional, null = university-wide)",
  "semester_id": "uuid",
  "name": "string",
  "amount": "number (> 0)",
  "due_date": "date"
}
```
- **Response Body (201):** created fee structure object, plus `invoices_created: "integer"` (count of invoice rows generated by this call).
- **Validation:** VR-008 — `amount` must be positive; `semester_id` must reference an existing semester; `department_id` if provided must reference an existing department.
- **Invoice auto-generation** (resolved during the Milestone 8 pre-implementation review — see `Database_Design.md` §6.25's design note, confirmed with the user): creating a `fee_structure` immediately creates one `unpaid` `invoice` for every currently-**active** student with **≥1 `Enrollment`** in a `class_session` for `semester_id`, whose own `student.department_id` matches `department_id` (or every such student, if `department_id` is null). This is the only place `invoice` rows are created — no separate invoice-creation endpoint exists.
- **Possible Errors:** invalid `amount` (422); invalid `semester_id`/`department_id` (422); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `fee_structure`, `department`, `semester`, `student`, `enrollment`, `class_session`, `invoice` (auto-generated), `notification` (Milestone 9 dispatch).
- **Business Rules:** VR-008. **Notification dispatch (resolved during the Milestone 9 pre-implementation review, confirmed with the user):** once invoice auto-generation commits, a `fee_due` notification is created for each newly-invoiced Student and any Parent linked to them (FR-044/FR-052) reporting the amount and due date. This is an event-driven notification tied to invoice issuance — a scheduled day-before-due-date reminder is not implemented, since no scheduler/cron mechanism exists anywhere in this project and `BR-010` leaves the exact timing undefined.

### 6.3 `POST /fees/payments`

- **Purpose:** Admin records a payment against a student's fee structure. (FR-040)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "student_id": "uuid",
  "fee_structure_id": "uuid",
  "amount": "number (> 0)",
  "payment_date": "timestamp",
  "payment_method": "string (optional)"
}
```
- **Response Body (201):** created payment record.
- **Validation:** VR-008 — `amount` must be positive; overpayment is **strictly disallowed** (resolved during Milestone 8 implementation, per the Milestone 8 kickoff's explicit Fees Domain Requirements — closes this section's own previously-flagged "unresolved" note): a payment is rejected with 409 if it would push the invoice's cumulative paid total beyond `fee_structure.amount`, and a fully-`paid` invoice accepts no further payments at all (409). An invoice must already exist for the (`student_id`, `fee_structure_id`) pair (created by `POST /fees` — see §6.2) — 404 if none exists.
- **Possible Errors:** invalid `amount` (422); `student_id`/`fee_structure_id` not found (404); no invoice exists for this student/structure (404); invoice already fully paid (409); payment would exceed the outstanding balance (409); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `payment`, `fee_structure`, `student`, `invoice` (status recalculation — written immediately by this endpoint, per `Database_Design.md` §6.25's design note; payment rows themselves are immutable, no update/delete endpoint exists).
- **Business Rules:** VR-008.

### 6.4 `GET /fees/payments/{studentId}`

- **Purpose:** Retrieve payment history for a specific student. (FR-041)
- **Authentication Required:** Yes
- **User Roles:** Admin, Parent
- **Request Body:** none.
- **Response Body (200):**
```json
{
  "student_id": "uuid",
  "payments": [
    { "payment_id": "uuid", "amount": "number", "payment_date": "timestamp", "fee_structure_id": "uuid" }
  ]
}
```
- **Validation:** `{studentId}` valid UUID.
- **Possible Errors:** Student not found (404); caller is a Parent without a `parent_student_link` to `{studentId}` (403, per BR-007).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `payment`, `parent_student_link`.
- **Business Rules:** BR-007.

### 6.5 `GET /fees/invoices/{id}`

- **Purpose:** Download an invoice as PDF. (FR-042)
- **Authentication Required:** Yes
- **User Roles:** Student (own invoice only), Admin
- **Request Body:** none.
- **Response Body (200):** binary PDF stream, `Content-Type: application/pdf`.
- **Validation:** `{id}` must reference an existing invoice.
- **Possible Errors:** Invoice not found (404); Student requesting another student's invoice (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `invoice`, `fee_structure`, `student`.
- **Business Rules:** none beyond ownership.

### 6.6 `GET /fees/overdue`

- **Purpose:** List all overdue accounts. (FR-043)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `department_id` (optional), `semester_id` (optional).
- **Response Body (200):**
```json
{
  "overdue_accounts": [
    { "student_id": "uuid", "invoice_id": "uuid", "amount_due": "number", "due_date": "date", "days_overdue": "integer" }
  ]
}
```
- An account is "overdue" (included in this list) when its invoice's stored `status` is `unpaid` or `partially_paid` **and** `due_date` is in the past — computed at read time, per `Database_Design.md` §6.25's design note; no grace period is applied (resolved during Milestone 8 implementation: `Requirement_Analysis.md` BR-010 leaves the exact grace period undefined, so the simplest documented reading — overdue starting the day after `due_date` — is used, consistent with not inventing an unstated grace window). `amount_due = fee_structure.amount - sum(payments for that student/fee_structure)`.
- **Validation:** none beyond query param types.
- **Possible Errors:** caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden.
- **Database Tables Used:** `invoice`, `fee_structure`, `student`, `payment`.
- **Business Rules:** BR-010 (overdue determination relative to `due_date`; exact grace period undefined — flagged in `Requirement_Analysis.md` §14).

### 6.7 `POST /fees/overdue/notify` *(gap-fill endpoint — not listed in proposal §6)*

- **Purpose:** Admin manually triggers an overdue fee notice, for a single student or in bulk for every account currently listed by `GET /fees/overdue`. (FR-056)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "student_ids": ["uuid"],
  "scope": "selected | all_overdue"
}
```
- **Response Body (200):**
```json
{ "notified_count": "integer" }
```
- **Validation:** if `scope: "selected"`, `student_ids` must be non-empty and each must currently have an overdue invoice; if `scope: "all_overdue"`, `student_ids` is ignored.
- **Possible Errors:** a listed `student_id` has no overdue invoice (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `invoice`, `student`, `notification` (creates a `fee_due`-type notification per notified student).
- **Business Rules:** BR-010.
- **Note:** This endpoint is not present in the proposal's §6 API spec. The proposal's §5 Admin Fee management row states Admin can "send overdue notices" as a manual capability, distinct from FR-044's automatic reminders — this endpoint closes that gap (see `Requirement_Analysis.md` §14 item 16).

---

## 7. Scheduling

### 7.1 `GET /schedule/me`

- **Purpose:** Student or Teacher views own timetable. (FR-045)
- **Authentication Required:** Yes
- **User Roles:** Student, Teacher
- **Request Body:** none.
- **Response Body (200):**
```json
{
  "entries": [
    {
      "schedule_entry_id": "uuid",
      "class_session_id": "uuid",
      "course_name": "string",
      "room_name": "string",
      "day_of_week": "Mon | Tue | Wed | Thu | Fri | Sat | Sun",
      "start_time": "time",
      "end_time": "time"
    }
  ]
}
```
- **Validation:** none beyond authentication.
- **Possible Errors:** none beyond standard auth failures.
- **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `schedule_entry`, `class_session`, `room`, `enrollment` (Student) / `teacher` (Teacher).
- **Business Rules:** result scoped to caller's own enrollments/assignments (NFR-002).

### 7.2 `POST /schedule`

- **Purpose:** Admin creates a class schedule entry. (FR-046)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "class_session_id": "uuid",
  "room_id": "uuid",
  "teacher_id": "uuid",
  "day_of_week": "Mon | Tue | Wed | Thu | Fri | Sat | Sun",
  "start_time": "time",
  "end_time": "time"
}
```
- **Response Body (201):** created schedule entry.
- **Validation:** VR-007 — `start_time < end_time`; `class_session_id`/`room_id`/`teacher_id` must reference existing rows.
- **Possible Errors:** `start_time >= end_time` (422); conflicting room/teacher booking (409, per BR-005/NFR-015); referenced IDs not found (404); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `schedule_entry`, `class_session`, `room`, `teacher`.
- **Business Rules:** BR-005, VR-007.

### 7.3 `PUT /schedule/{id}`

- **Purpose:** Admin updates a schedule entry. (FR-047)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** same shape as `POST /schedule` (partial update allowed).
- **Response Body (200):** updated schedule entry.
- **Validation:** VR-007; conflict re-check against the new time/room/teacher combination.
- **Possible Errors:** Entry not found (404); new time creates a conflict (409); invalid time range (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `schedule_entry`, `notification` (Milestone 9 dispatch).
- **Business Rules:** BR-005, VR-007; triggers a `schedule_change` notification to affected students (via `enrollment`) **and the assigned Teacher** (via `schedule_entry.teacher_id`) once the update commits (FR-051, corrected during the Milestone 9 pre-implementation review to include Teacher, per `UI_Wireframes.md` §16's Role Visibility line — see `Requirement_Analysis.md`'s FR-051 correction).

### 7.4 `DELETE /schedule/{id}`

- **Purpose:** Admin removes a class from the schedule. (FR-048)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none.
- **Response Body (204):** no content.
- **Validation:** `{id}` must reference an existing schedule entry.
- **Possible Errors:** Entry not found (404); caller is not Admin (403).
- **Status Codes:** 204 No Content, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `schedule_entry`, `notification` (Milestone 9 dispatch).
- **Business Rules:** triggers a `schedule_change` notification to affected students and the assigned Teacher once the deletion commits (FR-051, same recipients correction as §7.3 above).

### 7.5 `GET /schedule/conflicts`

- **Purpose:** Detect scheduling conflicts (double-booked rooms/teachers). (FR-049)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `semester_id` (optional scope).
- **Response Body (200):**
```json
{
  "conflicts": [
    {
      "type": "room | teacher",
      "conflicting_entry_ids": ["uuid", "uuid"],
      "day_of_week": "string",
      "overlap_start": "time",
      "overlap_end": "time"
    }
  ]
}
```
- **Validation:** `semester_id` if provided must reference an existing semester.
- **Possible Errors:** invalid `semester_id` (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `schedule_entry`, `room`, `teacher`.
- **Business Rules:** BR-005, NFR-015.

### 7.6 `POST /schedule/change-requests` *(gap-fill endpoint — not listed in proposal §6)*

- **Purpose:** Teacher requests a change to their timetable, routed to Admin for confirmation. (FR-050)
- **Authentication Required:** Yes
- **User Roles:** Teacher
- **Request Body:**
```json
{
  "schedule_entry_id": "uuid",
  "requested_change": { "day_of_week": "string", "start_time": "time", "end_time": "time", "room_id": "uuid (optional)" }
}
```
- **Response Body (201):**
```json
{ "id": "uuid", "status": "pending", "created_at": "timestamp" }
```
- **Validation:** VR-007 on the requested change; `schedule_entry_id` must belong to the requesting Teacher.
- **Possible Errors:** Entry not found or not owned by caller (403/404); invalid requested time range (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
- **Database Tables Used:** `schedule_change_request`, `schedule_entry`.
- **Business Rules:** BR-004 — Teacher cannot directly modify their own schedule; this only creates a pending request.
- **Note:** This endpoint is not present in the proposal's §6 API spec. It is proposed here to close the gap identified in `Requirement_Analysis.md` §8 and implemented per `Implementation_Roadmap.md` Milestone 4 — flagged, not silently invented.

### 7.7 `POST /schedule/change-requests/{id}/resolve` *(gap-fill endpoint)*

- **Purpose:** Admin confirms or rejects a Teacher's schedule change request. (FR-050)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{ "decision": "approve | reject", "comment": "string (optional)" }
```
- **Response Body (200):**
```json
{ "id": "uuid", "status": "approved | rejected", "resolved_at": "timestamp" }
```
- **Validation:** request must be in `pending` status; if approved, the underlying schedule update must itself pass VR-007 and conflict checks (BR-005).
- **Possible Errors:** Request not found (404); request not `pending` (409); approval creates a new conflict (409); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `schedule_change_request`, `schedule_entry`.
- **Business Rules:** BR-004, BR-005.
- **Note:** Same gap-fill status as 7.6.

### 7.8 `POST /schedule/class-sessions` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** Admin creates a class session — an offering of a `Course` taught by a `Teacher` in a `Semester` (e.g., "CS101, Section A, Fall 2026"). Prerequisite for `POST /schedule` (a `schedule_entry` requires an existing `class_session_id`) and for `POST /schedule/enrollments`.
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "course_id": "uuid",
  "teacher_id": "uuid",
  "semester_id": "uuid",
  "section_label": "string"
}
```
- **Response Body (201):**
```json
{
  "id": "uuid",
  "course_id": "uuid",
  "teacher_id": "uuid",
  "semester_id": "uuid",
  "section_label": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```
- **Validation:** `course_id`, `teacher_id`, `semester_id` must each reference an existing row.
- **Possible Errors:** any referenced ID not found (422); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `class_session`, `course`, `teacher`, `semester`.
- **Business Rules:** none beyond referential validity.
- **Note:** Neither this endpoint nor `class_session` creation is described anywhere in the proposal. Added because `class_session` is a required foreign key throughout the Scheduling, Exams, and Attendance endpoints above with no other way to create one — confirmed with the user during the Milestone 4 pre-implementation review (Option 1 of two presented). Classified **Derived** (not Design Enhancement) — it is an unavoidable prerequisite for Required features (scheduling, exams, attendance), not a discretionary addition. See `Proposal_vs_Engineering_Additions.md`.

### 7.9 `POST /schedule/enrollments` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** Admin enrolls a Student into a `ClassSession`. Prerequisite for `GET /schedule/me` (Student view), attendance marking, and exam/result scoping, all of which read from `enrollment`.
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{
  "student_id": "uuid",
  "class_session_id": "uuid"
}
```
- **Response Body (201):**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "class_session_id": "uuid",
  "enrolled_at": "timestamp"
}
```
- **Validation:** `student_id` and `class_session_id` must each reference an existing row; duplicate enrollment is rejected (`Database_Design.md` §6.10's unique constraint on `(student_id, class_session_id)`).
- **Possible Errors:** referenced ID not found (422); duplicate enrollment (409); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `enrollment`, `student`, `class_session`.
- **Business Rules:** none beyond uniqueness and referential validity.
- **Note:** Same gap-fill/Derived status as 7.8 — `enrollment` has no creation endpoint anywhere in the source documents despite being required by `GET /schedule/me`'s own documented response shape (§7.1).

### 7.10 `GET /schedule/class-sessions/{class_session_id}/roster` *(Derived Engineering Addition — not in proposal §6)*

- **Purpose:** List students enrolled in a class session, so a Teacher can see a pre-populated roster before marking attendance. Added during the Milestone 5 pre-implementation review — `UI_Wireframes.md` §15 (Teacher: Attendance Marker) requires the roster to load with enrolled students shown before marking begins, but no endpoint anywhere returned this.
- **Authentication Required:** Yes
- **User Roles:** Teacher (only for a class session they are assigned to — ownership check, same pattern as `POST /schedule/change-requests`), Admin
- **Request Body:** none.
- **Response Body (200):**
```json
{
  "class_session_id": "uuid",
  "students": [
    { "student_id": "uuid", "first_name": "string", "last_name": "string" }
  ]
}
```
- **Validation:** `{class_session_id}` must reference an existing class session.
- **Possible Errors:** class session not found (404); caller is a Teacher not assigned to this class session (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `enrollment`, `student`, `class_session`.
- **Business Rules:** none beyond the ownership check.
- **Note:** Classified Derived (unavoidable plumbing for the Milestone 5 Attendance Marker workflow, per `Proposal_vs_Engineering_Additions.md`), not Required — no proposal sentence names a roster-listing capability. Implemented via the schedule router/service (not the attendance domain) since it operates on `enrollment`/`class_session`, both owned by Scheduling.

---

## 8. Notifications *(gap-fill module — not listed in proposal §6)*

> **Note:** The proposal specifies a Notifications feature (§3) and screen (§7) but defines no corresponding API endpoints in §6. The two endpoints below are proposed to close that gap, consistent with `Requirement_Analysis.md` §14 item 3 and `Implementation_Roadmap.md` Milestone 9. They are documented here for completeness, not present in the original proposal text.

### 8.1 `GET /notifications`

- **Purpose:** Retrieve the authenticated user's notification feed. (FR-053)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:** none. Query params: `is_read` (optional filter), `page`, `page_size`.
- **Response Body (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "result_published | schedule_change | attendance_warning | fee_due | other",
      "message": "string",
      "is_read": "boolean",
      "created_at": "timestamp"
    }
  ],
  "unread_count": "integer",
  "total": "integer"
}
```
- **Validation:** none beyond authentication.
- **Possible Errors:** none beyond standard auth failures.
- **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `notification`.
- **Business Rules:** always scoped to the caller's own `user_id` (NFR-002/NFR-003).

### 8.2 `PUT /notifications/{id}/read`

- **Purpose:** Mark a notification as read. (FR-053)
- **Authentication Required:** Yes
- **User Roles:** All roles (own notification only)
- **Request Body:** none.
- **Response Body (200):**
```json
{ "id": "uuid", "is_read": true }
```
- **Validation:** `{id}` must reference a notification belonging to the caller.
- **Possible Errors:** Notification not found or not owned by caller (404); already read (200, idempotent).
- **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found.
- **Database Tables Used:** `notification`.
- **Business Rules:** ownership check (ownership, not role, governs access here).

### 8.3 Notification Triggers, Recipients, and Message Templates (Milestone 9)

Per the Milestone 9 mandatory Domain Rules (`message` must originate from a server-side template, never a frontend-generated string; dispatch must occur only after the originating transaction commits), the four automatic notification triggers are:

| Trigger | Originating Endpoint | `type` | Recipients | Message Template |
|---|---|---|---|---|
| Result published | `POST /results/{id}/approve` (`decision: approve`) | `result_published` | Student (the result's own student) | `"Result published: {course_name} {semester_name}"` |
| Schedule change | `PUT /schedule/{id}`, `DELETE /schedule/{id}` | `schedule_change` | Students enrolled in the entry's `class_session`, and the entry's assigned Teacher (corrected during this milestone's review — see `Requirement_Analysis.md` FR-051) | `"Schedule change: {course_name} moved to {room_name}"` (update) / `"Schedule change: {course_name} class cancelled"` (delete) |
| Low attendance warning | `POST /attendance` | `attendance_warning` | The marked Student, only on a threshold crossing from `>= 80%` to `< 80%` (resolved during this milestone's pre-implementation review, confirmed with the user — not repeated while the student remains below 80%) | `"Attendance warning: {course_name} below 80%"` |
| Fee due | `POST /fees` (invoice auto-generation) | `fee_due` | Each newly-invoiced Student, and any Parent linked to them | `"Fee due: {amount} due {due_date}"` |

No other automatic triggers exist (Domain Rule 19 — automatic notifications are only triggered by these four documented business events). Exam-domain events (Milestone 6) do not have a separate notification — `result_published` above is the sole notification for the exam-grading-to-result pipeline (resolved during this milestone's pre-implementation review, confirmed with the user; no new `notification.type` value was added).

---

## 9. Reports *(gap-fill module — not listed in proposal §6)*

> **Note:** The proposal's §5 Admin "Reports" feature states Admin can "Generate attendance, result, and fee reports by department, semester, or individual student," but §6 only provides an endpoint for attendance (`GET /attendance/reports`, documented in §4.5 above). The two endpoints below close the result/fee reporting gap, consistent with `Requirement_Analysis.md` §14 item 15 and FR-054/FR-055.

### 9.1 `GET /results/reports`

- **Purpose:** Admin generates result reports (grade distributions, pass/fail counts) by department, semester, or student. (FR-054)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `department_id` (optional), `semester_id` (optional), `student_id` (optional).
- **Response Body (200):**
```json
{
  "scope": { "department_id": "uuid | null", "semester_id": "uuid | null", "student_id": "uuid | null" },
  "grade_distribution": [
    { "grade_letter": "string", "count": "integer" }
  ],
  "pass_count": "integer",
  "fail_count": "integer",
  "average_gpa": "number"
}
```
- **Validation:** `department_id`/`semester_id`/`student_id` if provided must reference existing rows.
- **Possible Errors:** invalid filter IDs (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `course`, `department`, `semester`, `student`.
- **Business Rules:** BR-002 — only `published` results are included in report aggregates. `pass_count`/`fail_count` is determined by `grade_point > 0` (pass) vs. `grade_point == 0` (fail), since `grade_letter` is Teacher-supplied free text with no fixed enum (Milestone 10 engineering decision — see `Proposal_vs_Engineering_Additions.md`). `average_gpa` (Milestone 10, additive field, Finding A) is the same credit-hour-weighted GPA formula already implemented for `GET /results/me` (§5.x) — computed once in `result_service.compute_credit_weighted_gpa` and reused here, never duplicated, per this milestone's approved Finding A.

### 9.2 `GET /fees/reports`

- **Purpose:** Admin generates fee/revenue reports (collected, outstanding, overdue totals) by department, semester, or student. (FR-055)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none. Query params: `department_id` (optional), `semester_id` (optional), `student_id` (optional).
- **Response Body (200):**
```json
{
  "scope": { "department_id": "uuid | null", "semester_id": "uuid | null", "student_id": "uuid | null" },
  "total_collected": "number",
  "total_outstanding": "number",
  "total_overdue": "number"
}
```
- **Validation:** `department_id`/`semester_id`/`student_id` if provided must reference existing rows.
- **Possible Errors:** invalid filter IDs (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `payment`, `fee_structure`, `invoice`, `department`, `semester`, `student`.
- **Business Rules:** NFR-016 (computed on demand, not cached).

---

## 10. Reference Data (Department, Course, Room, Semester) *(gap-fill domain — not listed in proposal §6)*

> **Note:** The proposal never names Department, Course, Room, or Semester as standalone API resources, and §6 has no corresponding endpoints. But every Required feature that references a department, course, room, or semester (student/teacher creation, scheduling, fee structures, results) needs somewhere to source those IDs from — this domain is classified **Derived** in `docs/Proposal_vs_Engineering_Additions.md` ("Reference data CRUD" entry), not Required or Design Enhancement: it is an unavoidable mechanical prerequisite, not a feature the proposal asked for. Scope is deliberately minimal per `Implementation_Roadmap.md` Milestone 1 ("basic Admin CRUD to unblock later milestones") — list, create, and get-by-id only; update/delete are not implemented in Milestone 1 since nothing yet needs to edit or remove reference data.
>
> **Auth note (updated, Milestone 2):** These endpoints were unauthenticated in Milestone 1 (tracked as a known, temporary state — see `PROJECT_PROGRESS.md` M1 Known Issues) and are now retrofitted with RBAC now that Milestone 2 (Authentication & Authorization) has landed, per `System_Architecture.md` §6. Read endpoints (list, get-by-id) require authentication but accept **any** authenticated role — this is lookup data every role needs, and the proposal never restricted reads. Create endpoints are **Admin**-only, completing the "User Roles (intended): Admin" already documented for them since Milestone 1.

### 10.1 `GET /departments`
- **Purpose:** List all departments. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Request Body:** none. Query params: `page`, `page_size`.
- **Response Body (200):** `{ "items": [{ "id": "uuid", "name": "string", "code": "string", "created_at": "timestamp", "updated_at": "timestamp" }], "total": "integer", "page": "integer", "page_size": "integer" }`
- **Validation:** none beyond query param types.
- **Possible Errors:** missing/invalid token (401).
- **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `department`.
- **Business Rules:** none.

### 10.2 `POST /departments`
- **Purpose:** Create a department. **Authentication Required:** Yes. **User Roles:** Admin.
- **Request Body:** `{ "name": "string", "code": "string" }`
- **Response Body (201):** created department object (see 10.1 shape).
- **Validation:** `name` and `code` required, non-empty; both unique (`Database_Design.md` §10).
- **Possible Errors:** missing/invalid token (401); caller is not Admin (403); duplicate `name` or `code` (409); missing/empty fields (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `department`.
- **Business Rules:** none.

### 10.3 `GET /departments/{id}`
- **Purpose:** Retrieve a single department. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Response Body (200):** department object. **Possible Errors:** missing/invalid token (401); not found (404). **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found. **Database Tables Used:** `department`.

### 10.4 `GET /courses`
- **Purpose:** List all courses. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Request Body:** none. Query params: `department_id` (optional filter), `page`, `page_size`.
- **Response Body (200):** `{ "items": [{ "id": "uuid", "department_id": "uuid", "name": "string", "code": "string", "credit_hours": "integer", "created_at": "timestamp", "updated_at": "timestamp" }], "total": "integer", "page": "integer", "page_size": "integer" }`
- **Validation:** `department_id` if provided must reference an existing department.
- **Possible Errors:** missing/invalid token (401); invalid `department_id` (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `course`, `department`.

### 10.5 `POST /courses`
- **Purpose:** Create a course. **Authentication Required:** Yes. **User Roles:** Admin.
- **Request Body:** `{ "department_id": "uuid", "name": "string", "code": "string", "credit_hours": "integer" }`
- **Response Body (201):** created course object.
- **Validation:** all fields required; `code` unique; `department_id` must reference an existing department.
- **Possible Errors:** missing/invalid token (401); caller is not Admin (403); duplicate `code` (409); invalid/nonexistent `department_id` (422); missing fields (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `course`, `department`.

### 10.6 `GET /courses/{id}`
- **Purpose:** Retrieve a single course. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Response Body (200):** course object. **Possible Errors:** missing/invalid token (401); not found (404). **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found. **Database Tables Used:** `course`.

### 10.7 `GET /rooms`
- **Purpose:** List all rooms. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Request Body:** none. Query params: `page`, `page_size`.
- **Response Body (200):** `{ "items": [{ "id": "uuid", "name": "string", "building": "string | null", "capacity": "integer | null" }], "total": "integer", "page": "integer", "page_size": "integer" }`
- **Possible Errors:** missing/invalid token (401). **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `room`.

### 10.8 `POST /rooms`
- **Purpose:** Create a room. **Authentication Required:** Yes. **User Roles:** Admin.
- **Request Body:** `{ "name": "string", "building": "string (optional)", "capacity": "integer (optional)" }`
- **Response Body (201):** created room object.
- **Validation:** `name` required, unique.
- **Possible Errors:** missing/invalid token (401); caller is not Admin (403); duplicate `name` (409); missing `name` (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `room`.

### 10.9 `GET /rooms/{id}`
- **Purpose:** Retrieve a single room. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Response Body (200):** room object. **Possible Errors:** missing/invalid token (401); not found (404). **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found. **Database Tables Used:** `room`.

### 10.10 `GET /semesters`
- **Purpose:** List all semesters. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Request Body:** none. Query params: `page`, `page_size`.
- **Response Body (200):** `{ "items": [{ "id": "uuid", "name": "string", "start_date": "date", "end_date": "date" }], "total": "integer", "page": "integer", "page_size": "integer" }`
- **Possible Errors:** missing/invalid token (401). **Status Codes:** 200 OK, 401 Unauthorized.
- **Database Tables Used:** `semester`.

### 10.11 `POST /semesters`
- **Purpose:** Create a semester. **Authentication Required:** Yes. **User Roles:** Admin.
- **Request Body:** `{ "name": "string", "start_date": "date", "end_date": "date" }`
- **Response Body (201):** created semester object.
- **Validation:** `name` required, unique; `start_date < end_date` (`Database_Design.md` §10 check constraint).
- **Possible Errors:** missing/invalid token (401); caller is not Admin (403); duplicate `name` (409); `start_date >= end_date` (422); missing fields (422).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `semester`.

### 10.12 `GET /semesters/{id}`
- **Purpose:** Retrieve a single semester. **Authentication Required:** Yes. **User Roles:** Any authenticated role (Student, Teacher, Parent, Admin).
- **Response Body (200):** semester object. **Possible Errors:** missing/invalid token (401); not found (404). **Status Codes:** 200 OK, 401 Unauthorized, 404 Not Found. **Database Tables Used:** `semester`.

---

## Summary

| Domain | Endpoints Documented |
|---|---|
| Authentication | 4 |
| Users & Profiles | 10 |
| Exams & Grading | 8 |
| Attendance | 5 |
| Results & Transcripts | 4 |
| Fees (Optional, incl. 1 gap-fill) | 7 |
| Scheduling (incl. 2 gap-fill) | 7 |
| Notifications (gap-fill) | 2 |
| Reports (gap-fill) | 2 |
| Reference Data (gap-fill, Derived) | 12 |
| **Total** | **61** |

**Gap-fill endpoints** (7.6, 7.7, 8.1, 8.2, 6.7, 9.1, 9.2, and all of §10 — 19 total) are not present in the proposal's own §6 API specification. The first seven are required to satisfy features (FR-050, FR-052, FR-053, FR-054, FR-055, FR-056) that the proposal does describe elsewhere (classification: Required). Section 10's twelve Reference Data endpoints are different in kind — the proposal never describes Department/Course/Room/Semester management as a feature at all; they exist purely as unavoidable plumbing for other Required features (classification: Derived). Each is explicitly marked above rather than silently merged into the "official" list, consistent with the traceability approach in `Requirement_Traceability_Matrix.md` and `Proposal_vs_Engineering_Additions.md`.
