# Screenshot Evidence Checklist

**Project:** University Management System (ICT Education)
**Version:** v2.4.1
**Package location:** `docs/submission/project_screen_shot/`

```
project_screen_shot/
├── raw/                    — untouched originals, unchanged filenames, in their 4 original role folders
├── final/                  — all 62 screenshots, renamed, flat, numbered for presentation order
├── presentation_order/     — 48-file curated subset copied from final/, ready to drag into PowerPoint
├── Screenshot_Rename_Map.csv
└── Screenshot_Evidence_Checklist.md   (this file)
```

No screenshot content was resized, cropped, recolored, compressed, or edited — only copied and renamed. `raw/` is preserved exactly as originally supplied and is never overwritten by any future pass.

---

## 1. Total Screenshots

**62 screenshots** captured and inventoried, all traced to a real, currently-implemented page or feature (no guessed content).

## 2. Screenshots by Role

| Role | Count | Primary (numbered) | Variant (lettered suffix) |
|---|---|---|---|
| Shared / Login | 4 | 1 | 3 |
| Admin | 32 | 16 | 16 |
| Teacher | 11 | 8 | 3 |
| Student | 11 | 10 | 1 |
| Parent | 8 | 8 | 0 |
| **Total** | **62** | **43** | **19** |

## 3. Duplicates / Near-Duplicates (kept, suffixed — none discarded)

All 19 "variant" screenshots below are **preserved in `final/`** with a lettered suffix on their parent's number, per your instruction to keep every piece of evidence rather than discard any.

| Primary | Variants kept alongside it | What the variant shows |
|---|---|---|
| 01_Login_Page | 01A/01B/01C | Same login page, different role's email prefilled |
| 03_Admin_User_Management | 03A | "New Student" creation modal |
| 04_Admin_User_Management_Teachers | 04A | "New Teacher" creation modal |
| 05_Admin_Departments | 05A | "New Department" modal |
| 06_Admin_Courses | 06A | "New Course" modal |
| 07_Admin_Rooms | 07A | "New Room" modal |
| 08_Admin_Semesters | 08A | "New Semester" modal |
| 09_Admin_Timetable | 09A, 09B | 09A = scrolled continuation (schedule entry, conflict detection); 09B = same page with visible browser chrome/zoom popup (lower quality, kept for completeness only) |
| 10_Admin_Exams | 10A | Same list, status-filter dropdown open |
| 11_Admin_Result_Approval | 11A | Same page, status-filter dropdown open |
| 12_Admin_Fee_Dashboard | 12A, 12B | Student-select and Fee-Structure-select dropdowns open |
| 13_Admin_Report_Attendance | 13A, 13B, 13C | Department / Semester / Student filter dropdowns open |
| 20_Teacher_Timetable | 20A | "Request Schedule Change" modal |
| 23_Teacher_Exam_Builder | 23A, 23B | Class-select and question-type-select dropdowns open |
| 26_Student_Profile_Academic_History | 26A | Unscrolled top-half of the same page (photo upload only) |

## 4. Critical Missing Screenshots

These cover features that are fully implemented and demoed elsewhere in the system, but have **zero visual evidence anywhere in the 62-file set**. Recommended to capture before final submission if at all possible.

- **Teacher Grading Interface** — award marks/feedback per question for a submitted answer. A major, distinctive feature with no screenshot at all.
- **Teacher Results view** — Teacher's own submitted course results (pre-approval). No screenshot.
- **Parent Notifications page** (`/notifications`) — every other role has this; Parent only has the embedded 3-item dashboard widget, not the full page.
- **Invoice / Fee Receipt (populated)** — both Student's and Parent's Fee Centre screenshots were captured in an **empty state** (0.00 balance, "No invoices yet"). No screenshot anywhere shows an actual invoice or a paid receipt, despite this being a documented, implemented feature (invoice PDF relabels itself "Fee Receipt" once paid).
- **Attendance PDF (opened)** — the PDF export button is visible in `13_Admin_Report_Attendance` and `37_Parent_Attendance_Table`, but no screenshot shows the resulting downloaded/opened PDF file.
- **Attendance Excel (opened)** — same gap; button visible, output file never captured.
- **Attendance CSV (opened)** — same gap; button visible in the Parent view, output file never captured.

## 5. Recommended Missing Screenshots (nice to have, not required)

- **Swagger / OpenAPI UI** (`/docs`)
- **GitHub repository home page**
- **GitHub Releases / Git tags list**
- **Test results** (`pytest` / `vitest` terminal output, all-passing summary)
- **System Architecture diagram**
- **ER Diagram** — note: `docs/submission/diagrams/ER_Diagram.png` already exists from a prior task and could be reused directly here rather than recaptured
- **Project structure** (folder tree)
- **Project report** (cover page / title)
- **Admin Result Approval → Review detail screen** — the "Review" button is visible in `11_Admin_Result_Approval` but the approve/reject detail screen itself was never captured
- **Live Exam Room** (student mid-attempt, timer running) — not captured for any role

## 6. Reserved Numbering — Technical Evidence (Still Recommended Before Final Submission)

Per your instruction, numbers **60–68 are reserved** for Technical Evidence. **None of these files currently exist** — no screenshots were invented to fill them. Capture and drop them directly into `final/` (and `presentation_order/` if desired) using these exact names when available:

| Reserved Filename | Content |
|---|---|
| 60_GitHub_Repository.jpg | Repository home page |
| 61_GitHub_Releases.jpg | Releases page |
| 62_Git_Tags.jpg | Tag list (v0.1 → v2.4.1) |
| 63_Swagger_API.jpg | `/docs` OpenAPI UI |
| 64_ER_Diagram.jpg | Entity-relationship diagram (reuse `docs/submission/diagrams/ER_Diagram.png` if suitable) |
| 65_System_Architecture.jpg | Architecture diagram |
| 66_Test_Results.jpg | `pytest`/`vitest` passing summary |
| 67_Project_Structure.jpg | Folder tree |
| 68_Project_Report.jpg | Report cover page |

## 7. Screenshots Selected for Presentation (`presentation_order/`)

**48 of 62** screenshots were selected — every primary numbered shot plus the modals/dropdowns that demonstrate real interactive workflow (e.g. "New Department", "Request Schedule Change"). Excluded: pure duplicate-state variants that add no new information (repeated filter dropdowns open on an otherwise-identical screen, and the lower-quality browser-chrome duplicate of the Timetable page). All excluded files remain fully available in `final/` for report or viva use.

Order: `01_Login_Page` → Admin (`02`–`17`) → Teacher (`18`–`24`) → Student (`25`–`33`) → Parent (`34`–`40`). Reports are folded into the Admin block (`13`–`15`) per the existing numbering. No Technical Evidence files are included, since none currently exist (see Section 6).

## 8. Screenshots Selected for Report

Recommend all 43 primary numbered screenshots (`01` through `40`, no letter suffix) plus these specific high-value variants:
- `09A_Admin_Timetable_Scheduling` (distinct content, not a true duplicate)
- `03A_Admin_New_Student`, `04A_Admin_New_Teacher`, `20A_Teacher_Schedule_Change_Request` (demonstrate workflows, not just filters)

Skip pure filter/dropdown variants (`10A`, `11A`, `12A/B`, `13A/B/C`, `23A/B`, `26A`, `09B`) in the written report — they add bulk without new information.

## 9. Screenshots Selected for Viva

Keep the **full `final/` set of 62** accessible during the viva, not just the presentation subset — an examiner's question may specifically target a filter/dropdown state (e.g. "show me the exam status options") that only exists in a lettered-suffix file. The single most important screenshot to have ready is `34_Parent_Dashboard.jpg` — it's the clearest evidence of the v2.4.1 Parent Upcoming Exams gap-closure, and the most likely subject of a pointed examiner question given it's the most recent code change.

## 10. Final Submission Readiness

| Aspect | Status |
|---|---|
| Every implemented core role/feature has at least one screenshot | ✅ Yes, with the exceptions listed in Section 4 |
| No duplicate evidence discarded | ✅ All 62 preserved in `final/` |
| Consistent, professional naming | ✅ Numbered, role-grouped, short filenames |
| Originals preserved unmodified | ✅ `raw/` untouched, never overwritten |
| Presentation-ready subset exists | ✅ `presentation_order/`, 48 files, drag-in-order |
| Technical evidence (GitHub/Swagger/ER/tests/architecture) | ❌ **Not yet captured** — reserved numbers 60–68 documented above |
| Grading, Teacher Results, Parent Notifications, Invoice/Receipt, PDF/Excel/CSV exports | ❌ **Not yet captured** — see Section 4 (Critical) |

**Overall assessment:** The application-functionality evidence (Admin/Teacher/Student/Parent core workflows) is **strong and near-complete** — 62 well-organized, real, non-guessed screenshots covering the large majority of the system. The package is **not yet fully submission-ready** in two specific respects: (1) the six Critical gaps in Section 4, most notably the complete absence of Grading, Parent Notifications, and any populated invoice/receipt evidence, which are all implemented, demoable features; and (2) the entire Technical Evidence category (Section 6) is currently empty. Neither gap requires new development — only additional screenshots of features that already work. Once those are captured and dropped into `final/`/`presentation_order/` using the reserved names above, the package will be complete.
