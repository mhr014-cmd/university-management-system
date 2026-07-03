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
- **Database Tables Used:** `user` (implicitly, to re-verify `is_active` status before issuing a new token).
- **Business Rules:** Refresh tokens are rotated on use (NFR-004) — the old refresh token is invalidated once a new one is issued.

### 1.3 `POST /auth/logout`

- **Purpose:** Invalidate the current session's refresh token. (FR-003)
- **Authentication Required:** Yes
- **User Roles:** All roles
- **Request Body:** none (or `{ "refresh_token": "string" }` if the refresh token must be explicitly revoked)
- **Response Body (204):** no content
- **Validation:** none beyond authentication.
- **Possible Errors:** Missing/invalid access token (401).
- **Status Codes:** 204 No Content, 401 Unauthorized.
- **Database Tables Used:** `user` (session/refresh-token revocation record, if tracked separately).
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
      "is_active": "boolean"
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

### 3.6 `POST /exams/{id}/submit`

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
- **Validation:** exam must be in `open` status and within `time_limit_minutes` of the student's `started_at`; one submission per student per exam (`exam_submission` uniqueness); one answer per question (`answer` uniqueness).
- **Possible Errors:** Exam not open (409); time limit exceeded (409); duplicate submission (409); exam/question not found (404); caller not enrolled in the exam's class (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `exam_submission`, `answer`, `exam`.
- **Business Rules:** VR-004 (time limit enforcement); one submission per student per exam.

### 3.7 `POST /exams/{id}/grade`

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

### 3.8 `GET /exams/{id}/results`

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
  "by_class_session": [
    {
      "class_session_id": "uuid",
      "course_name": "string",
      "percentage": "number",
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
- **Business Rules:** percentage computed on demand, never cached (NFR-016).

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
- **Database Tables Used:** `attendance_record`, `class_session`, `enrollment`.
- **Business Rules:** VR-005; triggers low-attendance warning evaluation (FR-031/BR-008).

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
    { "student_id": "uuid", "date": "date", "status": "present | absent | late | excused" }
  ]
}
```
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

- **Purpose:** Student's own results across all semesters, incl. GPA. (FR-033)
- **Authentication Required:** Yes
- **User Roles:** Student (also used, parent-scoped, for FR-037)
- **Request Body:** none. Query params: `semester_id` (optional).
- **Response Body (200):**
```json
{
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
- **Validation:** `semester_id` if provided must reference an existing semester.
- **Possible Errors:** invalid `semester_id` (422).
- **Status Codes:** 200 OK, 401 Unauthorized, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `semester`, `course`.
- **Business Rules:** BR-001/BR-002 — only `published` results are returned to Student/Parent callers.

### 5.2 `POST /results/{examId}/submit`

- **Purpose:** Teacher submits graded results for admin approval. (FR-034)
- **Authentication Required:** Yes
- **User Roles:** Teacher
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
- **Validation:** exam must be fully graded (all submissions have `question_grade` entries) before results can be submitted.
- **Possible Errors:** Exam not fully graded (409); exam not found (404); caller is not the exam's Teacher (403); results already submitted for this exam (409).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict.
- **Database Tables Used:** `result`, `exam`, `exam_submission`, `question_grade`.
- **Business Rules:** BR-002 — enters `submitted` status, not visible to Student/Parent yet.

### 5.3 `POST /results/{id}/approve`

- **Purpose:** Admin approves and publishes submitted results. (FR-035)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:**
```json
{ "decision": "approve | reject", "comment": "string (optional, required if reject)" }
```
- **Response Body (200):**
```json
{ "id": "uuid", "status": "published | rejected", "approved_at": "timestamp | null" }
```
- **Validation:** result must currently be in `submitted` status.
- **Possible Errors:** Result not found (404); result not in `submitted` status (409); caller is not Admin (403); `reject` decision missing a comment (422, if required by policy).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `result`.
- **Business Rules:** BR-002 — enforces the `submitted → approved/published` (or `→ rejected`) state transition; publication triggers a notification (FR-052).

### 5.4 `GET /results/{studentId}/transcript`

- **Purpose:** Download an official PDF transcript with university seal. (FR-036)
- **Authentication Required:** Yes
- **User Roles:** Student (own record only), Admin
- **Request Body:** none.
- **Response Body (200):** binary PDF stream, `Content-Type: application/pdf`.
- **Validation:** `{studentId}` must reference an existing, active student; only `published` results are included.
- **Possible Errors:** Student not found (404); caller is a Student requesting another student's transcript (403); no published results available yet (409, or an empty transcript — policy TBD).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `result`, `student`, `semester`, `course`.
- **Business Rules:** BR-002 — only published results appear on the transcript.

---

## 6. Fees (Optional Module)

### 6.1 `GET /fees/me`

- **Purpose:** Student or Parent retrieves fee status and payment history. (FR-038)
- **Authentication Required:** Yes
- **User Roles:** Student, Parent
- **Request Body:** none. Query params: `semester_id` (optional).
- **Response Body (200):**
```json
{
  "outstanding_balance": "number",
  "invoices": [
    { "invoice_id": "uuid", "amount": "number", "status": "unpaid | partially_paid | paid | overdue", "due_date": "date" }
  ],
  "payments": [
    { "payment_id": "uuid", "amount": "number", "payment_date": "timestamp" }
  ]
}
```
- **Validation:** none beyond authentication; Parent callers are scoped to their linked child/children.
- **Possible Errors:** none beyond standard auth failures.
- **Status Codes:** 200 OK, 401 Unauthorized.
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
- **Response Body (201):** created fee structure object.
- **Validation:** VR-008 — `amount` must be positive; `semester_id` must reference an existing semester; `department_id` if provided must reference an existing department.
- **Possible Errors:** invalid `amount` (422); invalid `semester_id`/`department_id` (422); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `fee_structure`, `department`, `semester`.
- **Business Rules:** VR-008.

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
- **Validation:** VR-008 — `amount` must be positive and, per policy, should not push the student's paid total beyond `fee_structure.amount` unless overpayment is explicitly permitted (unresolved — see `Requirement_Analysis.md` §14 item; must be confirmed before strict enforcement is implemented).
- **Possible Errors:** invalid `amount` (422); `student_id`/`fee_structure_id` not found (404); overpayment beyond structure amount, if disallowed (409); caller is not Admin (403).
- **Status Codes:** 201 Created, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.
- **Database Tables Used:** `payment`, `fee_structure`, `student`, `invoice` (status recalculation).
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
- **Validation:** none beyond query param types.
- **Possible Errors:** caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden.
- **Database Tables Used:** `invoice`, `fee_structure`, `student`.
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
- **Database Tables Used:** `schedule_entry`.
- **Business Rules:** BR-005, VR-007; triggers a schedule-change notification to affected students (FR-051).

### 7.4 `DELETE /schedule/{id}`

- **Purpose:** Admin removes a class from the schedule. (FR-048)
- **Authentication Required:** Yes
- **User Roles:** Admin
- **Request Body:** none.
- **Response Body (204):** no content.
- **Validation:** `{id}` must reference an existing schedule entry.
- **Possible Errors:** Entry not found (404); caller is not Admin (403).
- **Status Codes:** 204 No Content, 401 Unauthorized, 403 Forbidden, 404 Not Found.
- **Database Tables Used:** `schedule_entry`.
- **Business Rules:** triggers a schedule-change notification to affected students (FR-051).

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
  "fail_count": "integer"
}
```
- **Validation:** `department_id`/`semester_id`/`student_id` if provided must reference existing rows.
- **Possible Errors:** invalid filter IDs (422); caller is not Admin (403).
- **Status Codes:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.
- **Database Tables Used:** `result`, `department`, `semester`, `student`.
- **Business Rules:** BR-002 — only `published` results are included in report aggregates.

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
| **Total** | **49** |

**Gap-fill endpoints** (7.6, 7.7, 8.1, 8.2, 6.7, 9.1, 9.2 — 7 total) are not present in the proposal's own §6 API specification but are required to satisfy features (FR-050, FR-052, FR-053, FR-054, FR-055, FR-056) that the proposal does describe elsewhere. Each is explicitly marked above rather than silently merged into the "official" list, consistent with the traceability approach in `Requirement_Traceability_Matrix.md`. The Reports gap and the overdue-notify gap were identified during the Project Readiness Audit (see `Requirement_Analysis.md` §14 items 15–16).
