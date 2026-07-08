// Profile page (FR-006, FR-007, FR-004, FR-008). Layout matches
// docs/UI_Wireframes.md Section 3: personal-info form + separate
// Change Password form. Department field only renders for Student/Teacher
// (Parent/Admin have no department_id — see app/schemas/user.py).
//
// Gap closure (post-M11 audit): the proposal (Section 3, Student — Profile)
// promises a profile photo and academic history "alongside profile data";
// Section 4 (Teacher — Profile & courses) promises assigned courses. Photo
// upload reuses the existing PUT /users/me profile_photo_url field (no new
// endpoint) — the file is resized/compressed client-side into a small data
// URI, since profile_photo_url is a plain string column with no dedicated
// object-storage endpoint (see docs/Proposal_vs_Engineering_Additions.md).
// Academic history reuses GET /results/me; assigned courses reuses
// GET /schedule/me (deduplicated by course) — both endpoints already
// existed, so this section adds no new API surface, only frontend
// composition.

import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, Camera } from "lucide-react";
import { useMe, useUpdateMe } from "../../features/users";
import { useChangePassword } from "../../features/auth";
import { useMyResults } from "../../features/results";
import { useMySchedule } from "../../features/schedule";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card, CardTitle } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageLoader } from "../../components/ui/PageLoader";
import { PasswordInput } from "../../components/ui/PasswordInput";
import { useToast } from "../../components/ui/Toast";
import { inputClass, labelClass } from "../../components/ui/classNames";

const MAX_PHOTO_SOURCE_BYTES = 5 * 1024 * 1024; // 5MB — original file, before client-side compression
const PHOTO_MAX_DIMENSION = 256;

function resizeImageToDataUri(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the selected file."));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("Could not read the selected image."));
      img.onload = () => {
        const scale = Math.min(1, PHOTO_MAX_DIMENSION / Math.max(img.width, img.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Canvas is not supported in this browser."));
          return;
        }
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.85));
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  });
}

function ErrorAlert({ children }: { children: React.ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

export default function ProfilePage() {
  const { showSuccess, showError } = useToast();
  const { data: me, isLoading } = useMe();
  const updateMe = useUpdateMe();
  const changePassword = useChangePassword();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const photoInputRef = useRef<HTMLInputElement>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);

  useEffect(() => {
    if (me) {
      setFirstName(me.profile.first_name);
      setLastName(me.profile.last_name);
    }
  }, [me]);

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setProfileError(null);
    if (firstName.trim().length === 0 || lastName.trim().length === 0) {
      setProfileError("First and last name are required.");
      return;
    }
    try {
      await updateMe.mutateAsync({ first_name: firstName, last_name: lastName });
      showSuccess("Profile updated.");
    } catch {
      setProfileError("Could not update profile. Please try again.");
    }
  };

  const handlePhotoSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file later
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      showError("Please select an image file.");
      return;
    }
    if (file.size > MAX_PHOTO_SOURCE_BYTES) {
      showError("Image is too large — please choose a file under 5MB.");
      return;
    }

    setIsUploadingPhoto(true);
    try {
      const dataUri = await resizeImageToDataUri(file);
      await updateMe.mutateAsync({ profile_photo_url: dataUri });
      showSuccess("Profile photo updated.");
    } catch {
      showError("Could not update your profile photo. Please try again.");
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setPasswordError(null);
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword });
      showSuccess("Password updated.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        setPasswordError("Current password is incorrect.");
      } else if (isAxiosError(error) && error.response?.status === 422) {
        setPasswordError("New password must differ from the current password and meet the minimum length.");
      } else {
        setPasswordError("Could not update password. Please try again.");
      }
    }
  };

  if (isLoading || !me) {
    return <PageLoader label="Loading profile..." />;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Profile</h1>
        <Badge tone="blue">{me.role}</Badge>
      </div>

      <Card>
        <form onSubmit={handleProfileSubmit} className="space-y-4">
          {profileError && <ErrorAlert>{profileError}</ErrorAlert>}

          {/* Photo upload only rendered for Student/Teacher — profile_photo_url
              has no column on parent/admin (Database_Design.md §6.4/§6.5),
              and user_service.update_me silently ignores it for those roles. */}
          {(me.role === "student" || me.role === "teacher") && (
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800">
                {me.profile.profile_photo_url ? (
                  <img
                    src={me.profile.profile_photo_url}
                    alt="Profile"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <Camera className="h-6 w-6 text-slate-400 dark:text-slate-500" aria-hidden="true" />
                )}
              </div>
              <div>
                <input
                  ref={photoInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePhotoSelected}
                />
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  isLoading={isUploadingPhoto}
                  onClick={() => photoInputRef.current?.click()}
                >
                  Change Photo
                </Button>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">JPEG/PNG, up to 5MB.</p>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="first_name" className={labelClass}>
              First Name <span className="text-red-500">*</span>
            </label>
            <input id="first_name" required value={firstName} onChange={(e) => setFirstName(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label htmlFor="last_name" className={labelClass}>
              Last Name <span className="text-red-500">*</span>
            </label>
            <input id="last_name" required value={lastName} onChange={(e) => setLastName(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label htmlFor="email" className={labelClass}>Email</label>
            <input id="email" value={me.email} disabled className={inputClass} />
          </div>
          {/* Department only rendered for Student/Teacher — Parent/Admin have no department_id (VR-009, read-only regardless). */}
          {me.profile.department_id && (
            <div>
              <label htmlFor="department" className={labelClass}>Department</label>
              <input id="department" value={me.profile.department_name ?? "—"} disabled className={inputClass} />
            </div>
          )}

          <Button type="submit" isLoading={updateMe.isPending}>Save Changes</Button>
        </form>
      </Card>

      <Card>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Change Password</h2>

          {passwordError && <ErrorAlert>{passwordError}</ErrorAlert>}

          <div>
            <label htmlFor="current_password" className={labelClass}>Current Password</label>
            <PasswordInput
              id="current_password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div>
            <label htmlFor="new_password" className={labelClass}>New Password</label>
            <PasswordInput
              id="new_password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label htmlFor="confirm_password" className={labelClass}>Confirm Password</label>
            <PasswordInput
              id="confirm_password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>

          <Button type="submit" isLoading={changePassword.isPending}>Update Password</Button>
        </form>
      </Card>

      {me.role === "student" && <AcademicHistorySection />}
      {me.role === "teacher" && <AssignedCoursesSection />}
    </div>
  );
}

// FR-008: Student academic history "alongside profile data" — reuses
// GET /results/me (Results View's own data source), no new endpoint.
function AcademicHistorySection() {
  const { data, isLoading } = useMyResults();
  const semesters = data?.semesters ?? [];

  return (
    <Card>
      <CardTitle>Academic History</CardTitle>
      {isLoading ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Loading academic history...</p>
      ) : semesters.length === 0 ? (
        <EmptyState title="No published results yet" description="Your semester grades and GPA will appear here once results are published." />
      ) : (
        <div className="mt-2 space-y-3">
          {semesters.map((semester) => (
            <div key={semester.semester_id} className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-900 dark:text-slate-100">{semester.semester_name}</span>
                <span className="text-slate-500 dark:text-slate-400">GPA: {semester.gpa.toFixed(2)}</span>
              </div>
              <ul className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {semester.courses.map((course) => (
                  <li key={course.course_id}>
                    {course.course_name} — {course.grade_letter}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

// Teacher — Profile & courses: "see their full teaching history" —
// reuses GET /schedule/me (Timetable's own data source), deduplicated by
// course. GET /schedule/me for a Teacher returns every schedule entry
// they've ever been assigned (schedule_repository.list_entries_for_teacher
// has no semester filter), so this is already the full teaching history,
// not just the current semester.
function AssignedCoursesSection() {
  const { data, isLoading } = useMySchedule();
  const courseNames = Array.from(new Set((data?.entries ?? []).map((e) => e.course_name))).sort();

  return (
    <Card>
      <CardTitle>Teaching History</CardTitle>
      {isLoading ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Loading teaching history...</p>
      ) : courseNames.length === 0 ? (
        <EmptyState title="No assigned courses yet" description="Courses you teach will appear here once scheduled." />
      ) : (
        <ul className="mt-2 list-inside list-disc text-sm text-slate-700 dark:text-slate-300">
          {courseNames.map((name) => (
            <li key={name}>{name}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}
