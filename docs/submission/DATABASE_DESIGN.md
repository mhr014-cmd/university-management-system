# Database Design (Summary)

> This is a reader-friendly summary for submission/evaluation. The full, authoritative schema document — every column, index rationale, and constraint — is [`docs/Database_Design.md`](../Database_Design.md). If anything here and that document ever appear to disagree, `docs/Database_Design.md` is correct.

## Overview

PostgreSQL, accessed exclusively through the SQLAlchemy ORM (no raw string-interpolated SQL anywhere in the codebase), with schema changes shipped as versioned Alembic migrations only — never hand-edited DDL against a running database.

- **26 tables**, normalized to **3rd Normal Form** — every non-key attribute depends on the key, the whole key, and nothing but the key.
- **10 sequential Alembic migrations**, single linear head (no branching), verified to produce an empty `autogenerate` diff against the current ORM models (i.e. the schema and the code that describes it never drift apart).
- Every table has a surrogate UUID primary key `id`, plus `created_at`/`updated_at` audit columns.

## Table list (grouped by domain)

| Domain | Tables |
|---|---|
| Identity | `user`, `student`, `teacher`, `parent`, `admin`, `parent_student_link` |
| Reference data | `department`, `course`, `room`, `semester` |
| Scheduling | `class_session`, `enrollment`, `schedule_entry`, `schedule_change_request` |
| Attendance | `attendance_record` |
| Exams | `exam`, `question`, `question_option`, `exam_submission`, `answer`, `question_grade` |
| Results | `result` |
| Fees | `fee_structure`, `payment`, `invoice` |
| Notifications | `notification` |

## Core relationships

- `user` is the base identity table (`email`, `password_hash`, `role`, `is_active`); `student`/`teacher`/`parent`/`admin` each extend it 1:1 with their own profile fields.
- `parent_student_link` is a many-to-many join between `parent` and `student` (a parent may be linked to multiple children; a child may — in principle — have multiple linked parents), with a unique constraint on `(parent_id, student_id)` so the same link can never be duplicated.
- `course` belongs to a `department`; `class_session` is a scheduled instance of a `course`, taught by one `teacher`, in one `semester`.
- `enrollment` joins `student` to `class_session` (unique per pair — a student can't be enrolled in the same class session twice).
- `schedule_entry` places a `class_session` into a `room` at a specific day/time, with its own `teacher_id`; `schedule_change_request` records a Teacher's proposed change to one `schedule_entry`, with a `pending`/`approved`/`rejected` status and (once resolved) which Admin resolved it and when.
- `exam` belongs to a `class_session`, created by a `teacher`; `question`/`question_option` belong to the exam; `exam_submission` links a `student` to an `exam`; `answer` belongs to a submission + question; `question_grade` holds a teacher's awarded marks/feedback for one answer.
- `attendance_record` ties a `student` + `class_session` + date to a status, recording which `teacher` marked it — unique per `(student_id, class_session_id, attendance_date)`, which is the actual database-level guarantee against duplicate attendance.
- `result` ties a `student` + `course` + `semester` to a grade/GPA and a `submitted`/`published`/`rejected` workflow status, recording the submitting teacher and (once approved) the approving admin — unique per `(student_id, course_id, semester_id)`, so at most one authoritative result exists per student/course/semester.
- `fee_structure` defines an amount/due-date for a department+semester; `invoice` is auto-generated per eligible student when a fee structure is created; `payment` records money received against an invoice, recorded by an admin.
- `notification` belongs to exactly one `user` — a Parent-linked event (e.g. `fee_due`) creates a **separate** notification row for each linked parent's own `user_id`, rather than the student's own notification somehow being visible to the parent.

## Referential integrity policy

- **Hard delete + `ON DELETE RESTRICT`** is the default for every foreign key — you cannot delete a `department` with existing `course` rows, a `course` with existing `enrollment`/`result` rows, and so on. This preserves every historical academic/financial record.
- **Exception:** a still-**draft** `exam`'s own `question`/`question_option` rows cascade-delete with it (deleting a draft's incomplete questions is expected); a **published** exam cannot be deleted at all — enforced at the service layer as a status check, not a foreign-key rule.
- **Identity records are deactivated, not deleted** — `user.is_active` governs login/authorization eligibility; Student/Teacher/Parent/Admin rows are never hard-deleted once they have any dependent data. This is deliberately **different** from the reference-data policy above: Department/Course/Room/Semester are catalog/lookup data (safe to hard-delete once unreferenced), while User/Student/Teacher/Parent are identity/audit records (never deleted, only deactivated).

## Key uniqueness constraints

| Table | Unique on | Purpose |
|---|---|---|
| `user` | `email` | one account per email |
| `department` | `name`, `code` | no duplicate departments |
| `course` | `code` | no duplicate course codes |
| `room` | `name` | no duplicate rooms |
| `semester` | `name` | no duplicate semesters |
| `enrollment` | `(student_id, class_session_id)` | no duplicate enrollment |
| `exam_submission` | `(exam_id, student_id)` | one submission per student per exam |
| `answer` | `(submission_id, question_id)` | one answer per question |
| `attendance_record` | `(student_id, class_session_id, attendance_date)` | no duplicate attendance |
| `result` | `(student_id, course_id, semester_id)` | one authoritative result per course/semester |
| `parent_student_link` | `(parent_id, student_id)` | no duplicate parent-child links |

Schedule conflict prevention (`schedule_entry`) combines a database unique index on `(room_id, day_of_week, start_time)` / `(teacher_id, day_of_week, start_time)` with a service-layer overlap check, since exact-start-time uniqueness alone cannot catch two entries that overlap on offset (not identical) start times.

## Computed, never stored, values

Attendance percentage, per-semester GPA, and outstanding fee balance are **always computed live at query time** from the underlying `attendance_record`/`result`/`payment` rows — never cached or denormalized as a stored column. This guarantees these figures can never silently drift out of sync with the records they're derived from.

## Indexing

Beyond automatic primary-key indexes, the schema adds targeted indexes for every documented query pattern that would otherwise require a full table scan — e.g. `user.email` (login), `user.role` (RBAC filtering), `notification(user_id, is_read)` (unread-count queries), `result.status` (the Admin approval queue). The full index list with its per-index rationale is in `docs/Database_Design.md` §9.

See [`docs/Database_Design.md`](../Database_Design.md) for the complete column-by-column listing of all 26 tables, the full text-format ER diagram, and every check/domain constraint (e.g. `exam.time_limit_minutes > 0`, `schedule_entry.start_time < end_time`, `fee_structure.amount > 0`).
