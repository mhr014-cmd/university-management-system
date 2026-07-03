# Database Design Document
## University Management System (ICT Education) — PostgreSQL

**Source inputs:** `docs/product_proposal.pdf`, `docs/Requirement_Analysis.md`, `docs/System_Architecture.md`
**Scope:** Logical/physical database design only. No SQL (DDL/DML) is included in this document.

---

## 1. Entity Identification

Derived from the proposal's feature lists (§3–§5) and API specification (§6):

1. **User** — base identity shared by all roles (login credentials, role, active status)
2. **Student** — student-specific profile data
3. **Teacher** — teacher-specific profile data
4. **Parent** — parent-specific profile data
5. **Admin** — admin-specific profile data
6. **ParentStudentLink** — association between a Parent and their child/children
7. **Department**
8. **Course** — subject offered by a Department
9. **ClassSession** — a scheduled instance/section of a Course (referred to as "class" in the proposal)
10. **Enrollment** — association between a Student and a ClassSession
11. **Room** — physical/virtual space used for scheduling
12. **ScheduleEntry** — a timetable slot binding a ClassSession, Room, and Teacher to a time
13. **ScheduleChangeRequest** — a Teacher's request to modify their schedule, pending Admin confirmation
14. **Exam** — an assessment created by a Teacher for a ClassSession
15. **Question** — a single question belonging to an Exam
16. **QuestionOption** — an MCQ answer option belonging to a Question (only applicable to MCQ-type questions)
17. **ExamSubmission** — a Student's attempt at an Exam
18. **Answer** — a Student's response to a single Question within a Submission
19. **QuestionGrade** — Teacher's awarded marks/feedback for a single Answer
20. **Semester** — an academic term (e.g., Spring 2026)
21. **Result** — a Student's aggregated result for a Course/Semester, subject to an approval workflow
22. **AttendanceRecord** — a single present/absent record for a Student in a ClassSession on a date
23. **FeeStructure** — a defined fee amount for a Department/Semester (Optional module)
24. **Payment** — a recorded payment by a Student against a FeeStructure (Optional module)
25. **Invoice** — a billable statement generated from a FeeStructure/Payment state (Optional module)
26. **Notification** — a system-generated alert delivered to a User

---

## 2. Relationship Identification

| # | Relationship | Cardinality |
|---|---|---|
| R1 | User — Student | 1:1 (a Student row extends a User row) |
| R2 | User — Teacher | 1:1 |
| R3 | User — Parent | 1:1 |
| R4 | User — Admin | 1:1 |
| R5 | Parent — Student (via ParentStudentLink) | M:N |
| R6 | Department — Course | 1:N |
| R7 | Department — Teacher | 1:N (a teacher's home department) |
| R8 | Department — FeeStructure | 1:N |
| R9 | Course — ClassSession | 1:N |
| R10 | Teacher — ClassSession | 1:N (a teacher teaches many class sessions) |
| R11 | ClassSession — Enrollment — Student | M:N (via Enrollment) |
| R12 | ClassSession — ScheduleEntry | 1:N |
| R13 | Room — ScheduleEntry | 1:N |
| R14 | Teacher — ScheduleEntry | 1:N |
| R15 | ScheduleEntry — ScheduleChangeRequest | 1:N |
| R16 | Teacher — ScheduleChangeRequest | 1:N (requester) |
| R17 | Admin — ScheduleChangeRequest | 1:N (confirmer, nullable until resolved) |
| R18 | ClassSession — Exam | 1:N |
| R19 | Teacher — Exam | 1:N (creator) |
| R20 | Exam — Question | 1:N |
| R21 | Question — QuestionOption | 1:N (MCQ only) |
| R22 | Student — ExamSubmission | 1:N |
| R23 | Exam — ExamSubmission | 1:N |
| R24 | ExamSubmission — Answer | 1:N |
| R25 | Question — Answer | 1:N |
| R26 | Answer — QuestionGrade | 1:1 |
| R27 | Teacher — QuestionGrade | 1:N (grader) |
| R28 | Semester — Result | 1:N |
| R29 | Student — Result | 1:N |
| R30 | Course — Result | 1:N |
| R31 | Teacher — Result | 1:N (submitter) |
| R32 | Admin — Result | 1:N (approver, nullable until approved) |
| R33 | Student — AttendanceRecord | 1:N |
| R34 | ClassSession — AttendanceRecord | 1:N |
| R35 | Teacher — AttendanceRecord | 1:N (marked-by) |
| R36 | FeeStructure — Payment | 1:N |
| R37 | Student — Payment | 1:N |
| R38 | Admin — Payment | 1:N (recorded-by) |
| R39 | Student — Invoice | 1:N |
| R40 | FeeStructure — Invoice | 1:N |
| R41 | User — Notification | 1:N (recipient) |

---

## 3. Normalization to 3NF

Applied normalization process:

**1NF** — Every table has a primary key; all columns are atomic (e.g., no comma-separated lists — MCQ options are a separate `question_option` table rather than a delimited string; permissions/roles are represented via a single `role` enum column, not repeating groups).

**2NF** — Every table uses a single-column surrogate primary key (UUID/serial `id`), so partial-key dependency is not possible; all non-key columns depend on the whole key by construction. The one composite-uniqueness case (`enrollment`: student + class_session; `attendance_record`: student + class_session + date) is enforced via a unique constraint on the combination, not by making those columns the primary key — preserving 2NF while still preventing duplicates.

**3NF** — Transitive dependencies were removed by extracting entities whenever an attribute depended on another non-key attribute rather than directly on the primary key:
- `Department` was extracted out of `Course`/`Teacher` (a course's department name/head would otherwise be transitively dependent on `course.department_id` through `department`).
- `Room` was extracted out of `ScheduleEntry` (room capacity/building is a property of the Room, not the schedule slot).
- `Semester` was extracted out of `Result` (semester start/end dates are a property of the Semester, not of an individual result row).
- `FeeStructure` was extracted from `Payment`/`Invoice` (fee amount/description belongs to the structure, not to each payment).
- GPA/percentage values are **not stored as denormalized redundant columns** on `Student`; attendance percentage and GPA are derived at query time from `AttendanceRecord` and `Result` respectively, avoiding update anomalies (a stored, cached percentage would need to be kept in sync manually and could drift — violates 3NF in spirit even if technically a single-table column, since it's functionally dependent on data in another table).
- User identity fields (email, password_hash, role, is_active) live only in `User`; they are **not duplicated** into `Student`/`Teacher`/`Parent`/`Admin`, which instead hold only role-specific attributes and a foreign key back to `User`.

Result: the schema below is in 3NF — every non-key attribute is dependent on the key, the whole key, and nothing but the key, in every table.

---

## 4. Entity-Relationship Diagram (Text Format)

```
┌───────────────┐
│     User        │
│───────────────│
│ PK id            │
│    email         │
│    password_hash │
│    role           │
│    is_active      │
└───────┬───────┘
        │ 1:1 (role-specific extension)
   ┌────┼─────────┬─────────────┐
   ▼    ▼         ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Student │ │ Teacher │ │ Parent │ │  Admin  │
│────────│ │────────│ │────────│ │────────│
│PK id     │ │PK id     │ │PK id     │ │PK id     │
│FK user_id│ │FK user_id│ │FK user_id│ │FK user_id│
│   dept_id│─┐│FK dept_id│ └────────┘ └────────┘
└────┬───┘ │└────┬───┘
     │      │      │
     │      │      │ (FK, R7)
     │      │      ▼
     │      │  ┌────────────┐
     │      │  │ Department   │
     │      │  │────────────│
     │      │  │PK id          │
     │      │  └─────┬──────┘
     │      │        │ 1:N (R6)
     │      │        ▼
     │      │  ┌────────────┐
     │      │  │   Course     │
     │      │  │────────────│
     │      │  │PK id          │
     │      │  │FK department_id│
     │      │  └─────┬──────┘
     │      │        │ 1:N (R9)
     │      │        ▼
     │      │  ┌───────────────────┐
     │      └─▶│   ClassSession       │◀── (R10) Teacher
     │         │───────────────────│
     │         │PK id                  │
     │         │FK course_id           │
     │         │FK teacher_id          │
     │         └─────┬────────┬───────┘
     │                │        │
     │   (R11 via Enrollment)  │ (R12)
     │                │        ▼
     │                │  ┌───────────────┐     ┌────────┐
     │                │  │ ScheduleEntry   │────▶│  Room   │ (R13)
     │                │  │───────────────│     └────────┘
     │                │  │PK id              │
     │                │  │FK class_session_id│
     │                │  │FK room_id          │
     │                │  │FK teacher_id        │(R14)
     │                │  └─────┬────────┘
     │                │        │ 1:N (R15)
     │                │        ▼
     │                │  ┌────────────────────────┐
     │                │  │  ScheduleChangeRequest    │
     │                │  │────────────────────────│
     │                │  │PK id                        │
     │                │  │FK schedule_entry_id          │
     │                │  │FK requested_by_teacher_id (R16)│
     │                │  │FK confirmed_by_admin_id  (R17, nullable)│
     │                │  └────────────────────────┘
     │                ▼
     │         ┌────────────┐
     └────────▶│ Enrollment   │  (R11: composite unique student_id+class_session_id)
               │────────────│
               │PK id          │
               │FK student_id  │
               │FK class_session_id│
               └────────────┘

┌────────────┐        1:N (R18,R19)        ┌────────────┐
│ ClassSession │◀────────────────────────────│    Exam      │◀── Teacher (R19)
└────────────┘                              │────────────│
                                             │PK id          │
                                             │FK class_session_id│
                                             │FK created_by_teacher_id│
                                             └─────┬──────┘
                                                    │ 1:N (R20)
                                                    ▼
                                             ┌────────────┐
                                             │  Question    │
                                             │────────────│
                                             │PK id          │
                                             │FK exam_id     │
                                             └─────┬──────┘
                                          ┌─────────┴─────────┐
                                          │ 1:N (R21, MCQ only) │ 1:N (R25)
                                          ▼                     ▼
                                   ┌───────────────┐     ┌────────────┐
                                   │ QuestionOption  │     │   Answer     │
                                   └───────────────┘     │────────────│
                                                          │PK id          │
                                                          │FK question_id │
                                                          │FK submission_id│(R24)
                                                          └─────┬──────┘
                                                                │ 1:1 (R26)
                                                                ▼
                                                          ┌────────────┐
                                                          │QuestionGrade │
                                                          │────────────│
                                                          │PK id          │
                                                          │FK answer_id   │
                                                          │FK graded_by_teacher_id│(R27)
                                                          └────────────┘

Student (R22) ──1:N──▶ ExamSubmission ◀──1:N── Exam (R23)
                        │────────────│
                        │PK id          │
                        │FK student_id  │
                        │FK exam_id     │
                        └────────────┘

┌──────────┐  1:N (R28)  ┌────────────┐
│ Semester   │────────────▶│   Result     │
└──────────┘             │────────────│
Student (R29) ────1:N────▶│PK id          │
Course   (R30) ────1:N────▶│FK student_id  │
Teacher  (R31, submitter)─▶│FK course_id   │
Admin    (R32, approver, nullable)─▶│FK semester_id │
                          │FK submitted_by_teacher_id│
                          │FK approved_by_admin_id (nullable)│
                          └────────────┘

Student (R33) ──1:N──▶ AttendanceRecord ◀──1:N── ClassSession (R34)
                        │────────────────│
                        │PK id                │
                        │FK student_id        │
                        │FK class_session_id   │
                        │FK marked_by_teacher_id│(R35)
                        └────────────────┘  (composite unique: student+class_session+date)

┌─────────────┐  1:N (R8,R36,R40)  ┌────────┐   ┌─────────┐
│ Department     │───────────────────▶│FeeStructure│──▶│ Invoice   │
└─────────────┘                    │────────│   │─────────│
                                    │PK id      │   │PK id       │
                                    └───┬────┘   │FK student_id │(R39)
                                        │1:N(R36) │FK fee_structure_id│(R40)
                                        ▼         └─────────┘
                                  ┌────────────┐
                                  │  Payment     │
                                  │────────────│
                                  │PK id          │
                                  │FK student_id  │(R37)
                                  │FK fee_structure_id│
                                  │FK recorded_by_admin_id│(R38)
                                  └────────────┘

User (R41) ──1:N──▶ Notification
                     │────────────│
                     │PK id          │
                     │FK user_id     │
                     └────────────┘

Parent ──M:N── Student  (via ParentStudentLink, R5)
        │─────────────────│
        │PK id                │
        │FK parent_id         │
        │FK student_id        │
        └─────────────────┘  (composite unique: parent_id+student_id)
```

---

## 5. Table List

1. `user`
2. `student`
3. `teacher`
4. `parent`
5. `admin`
6. `parent_student_link`
7. `department`
8. `course`
9. `class_session`
10. `enrollment`
11. `room`
12. `schedule_entry`
13. `schedule_change_request`
14. `exam`
15. `question`
16. `question_option`
17. `exam_submission`
18. `answer`
19. `question_grade`
20. `semester`
21. `result`
22. `attendance_record`
23. `fee_structure`
24. `payment`
25. `invoice`
26. `notification`

---

## 6–8. Columns, Primary Keys, Foreign Keys

> Convention: every table has a surrogate primary key `id` (UUID). Audit columns `created_at`, `updated_at` are included on all tables for traceability, in line with the Logging/Audit strategy in System_Architecture.md §10.

### 6.1 `user`
| Column | Type (logical) | Notes |
|---|---|---|
| id | UUID | **PK** |
| email | string | unique, not null |
| password_hash | string | not null |
| role | enum(student, teacher, parent, admin) | not null |
| is_active | boolean | not null, default true — supports BR-006 deactivation |
| created_at | timestamp | not null |
| updated_at | timestamp | not null |

### 6.2 `student`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| user_id | UUID | **FK → user.id**, unique (1:1, R1) |
| department_id | UUID | **FK → department.id** (R part of R6 context) |
| first_name | string | not null |
| last_name | string | not null |
| profile_photo_url | string | nullable |
| date_of_birth | date | nullable |
| enrollment_date | date | not null |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.3 `teacher`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| user_id | UUID | **FK → user.id**, unique (R2) |
| department_id | UUID | **FK → department.id** (R7) |
| first_name | string | not null |
| last_name | string | not null |
| profile_photo_url | string | nullable |
| hire_date | date | nullable |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.4 `parent`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| user_id | UUID | **FK → user.id**, unique (R3) |
| first_name | string | not null |
| last_name | string | not null |
| phone_number | string | nullable |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.5 `admin`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| user_id | UUID | **FK → user.id**, unique (R4) |
| first_name | string | not null |
| last_name | string | not null |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.6 `parent_student_link`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| parent_id | UUID | **FK → parent.id** |
| student_id | UUID | **FK → student.id** |
| relationship_type | string | nullable (e.g., father, mother, guardian) |
| created_at | timestamp | |

### 6.7 `department`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| name | string | unique, not null |
| code | string | unique, not null |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.8 `course`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| department_id | UUID | **FK → department.id** |
| name | string | not null |
| code | string | unique, not null |
| credit_hours | integer | not null |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.9 `class_session`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| course_id | UUID | **FK → course.id** |
| teacher_id | UUID | **FK → teacher.id** |
| semester_id | UUID | **FK → semester.id** |
| section_label | string | not null (e.g., "Section A") |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.10 `enrollment`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| student_id | UUID | **FK → student.id** |
| class_session_id | UUID | **FK → class_session.id** |
| enrolled_at | timestamp | not null |
| Unique constraint | (student_id, class_session_id) | prevents duplicate enrollment |

### 6.11 `room`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| name | string | unique, not null |
| building | string | nullable |
| capacity | integer | nullable |

### 6.12 `schedule_entry`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| class_session_id | UUID | **FK → class_session.id** |
| room_id | UUID | **FK → room.id** |
| teacher_id | UUID | **FK → teacher.id** |
| day_of_week | enum(Mon..Sun) | not null |
| start_time | time | not null |
| end_time | time | not null |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.13 `schedule_change_request`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| schedule_entry_id | UUID | **FK → schedule_entry.id** |
| requested_by_teacher_id | UUID | **FK → teacher.id** |
| confirmed_by_admin_id | UUID | **FK → admin.id**, nullable until resolved |
| requested_change | string/JSON | not null (proposed new time/room) |
| status | enum(pending, approved, rejected) | not null, default pending |
| created_at | timestamp | |
| resolved_at | timestamp | nullable |

### 6.14 `exam`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| class_session_id | UUID | **FK → class_session.id** |
| created_by_teacher_id | UUID | **FK → teacher.id** |
| title | string | not null |
| exam_type | enum(mcq, written, practical_coding, mixed) | not null |
| time_limit_minutes | integer | not null, > 0 |
| status | enum(draft, scheduled, open, closed, published) | not null, default draft — supports BR-003 |
| scheduled_at | timestamp | nullable |
| created_at | timestamp | |
| updated_at | timestamp | |

**Terminology note (added during Project Readiness Audit):** The proposal's own UI description (§7: "Exam list — status badges (scheduled, open, graded, published)") uses "graded" where this schema uses `closed`. This is a deliberate refinement, not an inconsistency to carry into implementation: `closed` marks that the exam is no longer accepting submissions (a stored, exam-level fact), while "graded" is a derived, submission-level fact (whether every `exam_submission` for that exam has a `question_grade`) — it cannot be a single stored value on `exam` without risking staleness as submissions are graded one at a time. The frontend (`UI_Wireframes.md` §4) should compute a "Graded" display label from `closed` status + full-grading-completion check, rather than expecting `closed`/"graded" to be interchangeable strings.

### 6.15 `question`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| exam_id | UUID | **FK → exam.id** |
| question_text | text | not null |
| question_type | enum(mcq, short_answer, descriptive, coding) | not null |
| marks | numeric | not null, > 0 |
| hint | text | nullable |
| order_index | integer | not null |

### 6.16 `question_option`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| question_id | UUID | **FK → question.id** |
| option_text | string | not null |
| is_correct | boolean | not null |

### 6.17 `exam_submission`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| exam_id | UUID | **FK → exam.id** |
| student_id | UUID | **FK → student.id** |
| submitted_at | timestamp | nullable (null until submitted) |
| started_at | timestamp | not null |
| status | enum(in_progress, submitted, graded) | not null, default in_progress |
| Unique constraint | (exam_id, student_id) | one submission per student per exam |

### 6.18 `answer`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| submission_id | UUID | **FK → exam_submission.id** |
| question_id | UUID | **FK → question.id** |
| answer_text | text | nullable (answer body; MCQ stores selected option id) |
| selected_option_id | UUID | **FK → question_option.id**, nullable (MCQ only) |
| Unique constraint | (submission_id, question_id) | one answer per question per submission |

### 6.19 `question_grade`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| answer_id | UUID | **FK → answer.id**, unique (1:1, R26) |
| graded_by_teacher_id | UUID | **FK → teacher.id** |
| awarded_marks | numeric | not null, >= 0 |
| feedback | text | nullable |
| graded_at | timestamp | not null |

### 6.20 `semester`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| name | string | unique, not null (e.g., "Spring 2026") |
| start_date | date | not null |
| end_date | date | not null |

### 6.21 `result`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| student_id | UUID | **FK → student.id** |
| course_id | UUID | **FK → course.id** |
| semester_id | UUID | **FK → semester.id** |
| submitted_by_teacher_id | UUID | **FK → teacher.id** |
| approved_by_admin_id | UUID | **FK → admin.id**, nullable until approved |
| grade_letter | string | nullable until finalized |
| grade_point | numeric | nullable until finalized |
| status | enum(submitted, published, rejected) | not null, default submitted — supports BR-002 |
| submitted_at | timestamp | not null |
| approved_at | timestamp | nullable |
| Unique constraint | (student_id, course_id, semester_id) | one result per student per course per semester |

**Design note (added during Project Readiness Audit):** An earlier draft of this table included a standalone `approved` status value between `submitted` and `published`. It was removed because FR-035 / `POST /results/{id}/approve` (see `API_Contract.md` §5.3) performs approval and publication as a single atomic action — there is no proposal-defined endpoint that transitions a result to "approved" without simultaneously publishing it, so `approved` was an unreachable state. `approved_by_admin_id` and `approved_at` are retained as columns (they record who/when the single approve-and-publish action occurred) even though the status enum itself no longer has a separate `approved` value.

### 6.22 `attendance_record`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| student_id | UUID | **FK → student.id** |
| class_session_id | UUID | **FK → class_session.id** |
| marked_by_teacher_id | UUID | **FK → teacher.id** |
| attendance_date | date | not null |
| status | enum(present, absent, late, excused) | not null |
| Unique constraint | (student_id, class_session_id, attendance_date) | prevents duplicate marking (VR-005) |

### 6.23 `fee_structure`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| department_id | UUID | **FK → department.id**, nullable (may be university-wide) |
| semester_id | UUID | **FK → semester.id** |
| name | string | not null |
| amount | numeric | not null, > 0 |
| due_date | date | not null |
| created_at | timestamp | |

### 6.24 `payment`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| student_id | UUID | **FK → student.id** |
| fee_structure_id | UUID | **FK → fee_structure.id** |
| recorded_by_admin_id | UUID | **FK → admin.id** |
| amount | numeric | not null, > 0 |
| payment_date | timestamp | not null |
| payment_method | string | nullable |

### 6.25 `invoice`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| student_id | UUID | **FK → student.id** |
| fee_structure_id | UUID | **FK → fee_structure.id** |
| status | enum(unpaid, partially_paid, paid, overdue) | not null |
| issued_at | timestamp | not null |
| pdf_url | string | nullable (generated document reference) |

### 6.26 `notification`
| Column | Type | Notes |
|---|---|---|
| id | UUID | **PK** |
| user_id | UUID | **FK → user.id** |
| type | enum(result_published, schedule_change, attendance_warning, fee_due, other) | not null |
| message | text | not null |
| is_read | boolean | not null, default false |
| created_at | timestamp | not null |

---

## 9. Index Recommendations

Beyond the automatic indexes on every primary key:

| Table | Index | Reason |
|---|---|---|
| `user` | unique index on `email` | login lookups (FR-001) |
| `user` | index on `role` | RBAC filtering, admin listing by role |
| `student` | index on `department_id` | department-scoped queries/reports |
| `teacher` | index on `department_id` | department-scoped queries |
| `parent_student_link` | composite unique index on `(parent_id, student_id)` | prevents duplicate links, fast parent→children lookup |
| `parent_student_link` | index on `student_id` | reverse lookup (which parents belong to a student) |
| `course` | index on `department_id` | course-by-department listing |
| `class_session` | index on `(course_id, semester_id)` | timetable/enrollment queries |
| `class_session` | index on `teacher_id` | teacher's classes lookup |
| `enrollment` | composite unique index on `(student_id, class_session_id)` | prevents duplicate enrollment; supports `GET /schedule/me`, class roster queries |
| `schedule_entry` | composite unique index on `(room_id, day_of_week, start_time)` | conflict detection (BR-005, `GET /schedule/conflicts`) |
| `schedule_entry` | composite unique index on `(teacher_id, day_of_week, start_time)` | teacher double-booking prevention |
| `exam` | index on `class_session_id` | exam list per class |
| `exam` | index on `status` | filtering published/unpublished exams |
| `question` | index on `exam_id` | fetching exam questions in order |
| `exam_submission` | composite unique index on `(exam_id, student_id)` | one submission per student per exam; also supports grading queries |
| `answer` | composite unique index on `(submission_id, question_id)` | one answer per question |
| `attendance_record` | composite unique index on `(student_id, class_session_id, attendance_date)` | duplicate prevention + `GET /attendance/me` filtering |
| `attendance_record` | index on `(class_session_id, attendance_date)` | teacher marking/report queries |
| `result` | composite unique index on `(student_id, course_id, semester_id)` | duplicate prevention + `GET /results/me` |
| `result` | index on `status` | admin approval queue (`GET` pending results) |
| `payment` | index on `student_id` | `GET /fees/payments/{studentId}` |
| `payment` | index on `fee_structure_id` | revenue/overdue reporting |
| `invoice` | index on `(student_id, status)` | `GET /fees/overdue`, fee centre queries |
| `notification` | composite index on `(user_id, is_read)` | notification panel unread-count queries |
| `notification` | index on `created_at` | chronological feed ordering |

---

## 10. Constraints

### Entity Integrity
- Every table has a NOT NULL surrogate primary key (`id`).

### Referential Integrity
- All foreign keys listed in Section 6–8 are enforced with `ON DELETE RESTRICT` by default (e.g., cannot delete a `Department` with existing `Course` rows; cannot delete a `Course` with existing `Enrollment`/`Result` rows), preserving historical academic records per BR-006.
- Exception: `question_option` and `answer.selected_option_id`, and child rows of a still-**unpublished** `exam` (i.e., `question`, `question_option`) use `ON DELETE CASCADE` from their parent `exam`/`question`, since deleting a draft exam should remove its draft questions (consistent with BR-003 — published exams are delete-restricted at the service layer, not at the FK level, since "published" is a status value, not a structural property).

### Domain / Check Constraints
- `user.role` restricted to `{student, teacher, parent, admin}`.
- `exam.time_limit_minutes > 0`.
- `question.marks > 0`.
- `question_grade.awarded_marks >= 0` and, enforced at the service/business-logic layer (not a simple column check, since it requires comparing against `question.marks`), `awarded_marks <= question.marks` (VR-006).
- `fee_structure.amount > 0`; `payment.amount > 0`.
- `schedule_entry.start_time < end_time`.
- `semester.start_date < end_date`.

### Uniqueness Constraints
- `user.email` unique.
- `department.name`, `department.code` unique.
- `course.code` unique.
- `room.name` unique.
- `semester.name` unique.
- `enrollment (student_id, class_session_id)` unique.
- `exam_submission (exam_id, student_id)` unique.
- `answer (submission_id, question_id)` unique.
- `attendance_record (student_id, class_session_id, attendance_date)` unique.
- `result (student_id, course_id, semester_id)` unique.
- `schedule_entry (room_id, day_of_week, start_time)` unique — supports BR-005 room conflict prevention (combined with an overlap check at the service layer, since exact-start-time uniqueness alone does not catch overlapping-but-offset time ranges).
- `schedule_entry (teacher_id, day_of_week, start_time)` unique — supports teacher conflict prevention (same overlap-check caveat applies).
- `parent_student_link (parent_id, student_id)` unique.

### Nullable / Required Fields Summary
- Fields nullable only when the data is genuinely optional or represents a not-yet-reached workflow state (e.g., `result.approved_by_admin_id`, `result.approved_at`, `schedule_change_request.confirmed_by_admin_id` are null until the corresponding workflow step occurs).

### Deactivation, not Deletion
- `user.is_active` governs login/authorization eligibility (BR-006); Student/Teacher rows are never hard-deleted once they have any dependent Attendance/Result/Payment/Enrollment data, consistent with the `RESTRICT` delete policy above.

---

## 11. Seed Data Requirements

To support development, testing, and demoing the full feature set, the following seed data is required at minimum:

1. **Departments** — at least 2–3 (e.g., "Computer Science", "Business Administration") to demonstrate department-scoped filtering and reporting.
2. **Semesters** — at least 2 (one past/closed, one current) to demonstrate semester-scoped results and fee structures.
3. **Rooms** — at least 3–4, to demonstrate schedule conflict detection.
4. **Users/Admin** — at least 1 Admin account, seeded directly (cannot be self-registered, since `POST /users/students`/`/teachers` are Admin-only — the very first Admin must be seeded).
5. **Users/Teachers** — at least 2–3 Teacher accounts across different departments.
6. **Users/Students** — at least 5–10 Student accounts across different departments/semesters, including at least one with low attendance (to demonstrate warning logic) and one with an outstanding fee balance (to demonstrate overdue logic).
7. **Users/Parents** — at least 1–2 Parent accounts, each linked via `parent_student_link` to at least one seeded Student (including one parent linked to multiple children, to exercise the M:N relationship).
8. **Courses** — at least 3–5, distributed across the seeded departments.
9. **ClassSessions** — at least one section per seeded course, each assigned to a seeded Teacher and Semester.
10. **Enrollments** — seeded students enrolled into multiple class sessions, enough to populate a realistic timetable and attendance history.
11. **ScheduleEntries** — one per class session, deliberately including at least one intentional room/time overlap in a *staging/test* dataset only (not in the primary demo seed) to validate conflict detection.
12. **Exams** — at least one exam per class session in each state: `draft`, `scheduled`, `open/closed`, and `published`, to exercise every status transition and the `DELETE` restriction on published exams.
13. **Questions/QuestionOptions** — a mix of MCQ (with options), short-answer, descriptive, and coding questions across the seeded exams.
14. **ExamSubmissions/Answers/QuestionGrades** — at least one fully graded submission (to populate a published result and demonstrate transcript generation) and one ungraded/pending submission.
15. **AttendanceRecords** — a history of records across multiple dates per seeded enrollment, including enough absences for at least one seeded student to cross the low-attendance warning threshold (see Requirement_Analysis.md §14, item 4 — exact threshold value still needs confirmation before this seed can be made precise).
16. **Results** — seeded in each workflow state: `submitted` (pending admin review), `approved`, and `published`, to exercise the full approval workflow end-to-end.
17. **FeeStructures** — at least one per seeded department/semester combination.
18. **Payments/Invoices** — a mix of fully paid, partially paid, and overdue invoices per seeded student, to populate the Admin fee dashboard and `GET /fees/overdue`.
19. **Notifications** — at least one seeded notification per type (`result_published`, `schedule_change`, `attendance_warning`, `fee_due`) in both read and unread states, to populate the Notifications panel during UI development/testing.

**Note:** Items 11 (intentional schedule conflict) and 15/18 (threshold-dependent data) should be clearly separated into a distinct "test/demo" seed profile versus a "clean" baseline seed profile, so that automated tests can rely on deliberately invalid data while a stakeholder demo is not confused by a visibly conflicting timetable.
