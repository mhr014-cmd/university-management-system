// Profile page (FR-006, FR-007, FR-004). Layout matches
// docs/UI_Wireframes.md Section 3: personal-info form + separate
// Change Password form. Department field only renders for Student/Teacher
// (Parent/Admin have no department_id — see app/schemas/user.py).

import { useEffect, useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { useMe, useUpdateMe } from "../../features/users";
import { useChangePassword } from "../../features/auth";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { PageLoader } from "../../components/ui/PageLoader";
import { PasswordInput } from "../../components/ui/PasswordInput";
import { inputClass, labelClass } from "../../components/ui/classNames";

function ErrorAlert({ children }: { children: React.ReactNode }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

function SuccessAlert({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 px-3 py-2.5 text-sm text-green-700 dark:border-green-900 dark:bg-green-950/50 dark:text-green-300">
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

export default function ProfilePage() {
  const { data: me, isLoading } = useMe();
  const updateMe = useUpdateMe();
  const changePassword = useChangePassword();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  useEffect(() => {
    if (me) {
      setFirstName(me.profile.first_name);
      setLastName(me.profile.last_name);
    }
  }, [me]);

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setProfileMessage(null);
    setProfileError(null);
    if (firstName.trim().length === 0 || lastName.trim().length === 0) {
      setProfileError("First and last name are required.");
      return;
    }
    try {
      await updateMe.mutateAsync({ first_name: firstName, last_name: lastName });
      setProfileMessage("Profile updated.");
    } catch {
      setProfileError("Could not update profile. Please try again.");
    }
  };

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setPasswordMessage(null);
    setPasswordError(null);
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword });
      setPasswordMessage("Password updated.");
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
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Profile</h1>

      <Card>
        <form onSubmit={handleProfileSubmit} className="space-y-4">
          {profileMessage && <SuccessAlert>{profileMessage}</SuccessAlert>}
          {profileError && <ErrorAlert>{profileError}</ErrorAlert>}

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

          {passwordMessage && <SuccessAlert>{passwordMessage}</SuccessAlert>}
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
    </div>
  );
}
