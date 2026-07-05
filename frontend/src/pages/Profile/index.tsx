// Profile page (FR-006, FR-007, FR-004). Layout matches
// docs/UI_Wireframes.md Section 3: personal-info form + separate
// Change Password form. Department field only renders for Student/Teacher
// (Parent/Admin have no department_id — see app/schemas/user.py).

import { useEffect, useState, type FormEvent } from "react";
import { isAxiosError } from "axios";
import { useMe, useUpdateMe } from "../../features/users";
import { useChangePassword } from "../../features/auth";

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
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading profile...</p>;
  }

  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Profile</h1>

      <form onSubmit={handleProfileSubmit} className="space-y-4 rounded border border-slate-200 p-6 dark:border-slate-700">
        {profileMessage && (
          <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
            {profileMessage}
          </div>
        )}
        {profileError && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {profileError}
          </div>
        )}

        <div>
          <label htmlFor="first_name" className="mb-1 block text-sm font-medium">First Name</label>
          <input
            id="first_name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
        </div>
        <div>
          <label htmlFor="last_name" className="mb-1 block text-sm font-medium">Last Name</label>
          <input
            id="last_name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Email</label>
          <input value={me.email} disabled className="w-full rounded border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400" />
        </div>
        {/* Department only rendered for Student/Teacher — Parent/Admin have no department_id (VR-009, read-only regardless). */}
        {me.profile.department_id && (
          <div>
            <label className="mb-1 block text-sm font-medium">Department</label>
            <input value={me.profile.department_name ?? "—"} disabled className="w-full rounded border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400" />
          </div>
        )}

        <button
          type="submit"
          disabled={updateMe.isPending}
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {updateMe.isPending ? "Saving..." : "Save Changes"}
        </button>
      </form>

      <form onSubmit={handlePasswordSubmit} className="space-y-4 rounded border border-slate-200 p-6 dark:border-slate-700">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Change Password</h2>

        {passwordMessage && (
          <div className="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-800 dark:bg-green-950 dark:text-green-300">
            {passwordMessage}
          </div>
        )}
        {passwordError && (
          <div role="alert" className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
            {passwordError}
          </div>
        )}

        <div>
          <label htmlFor="current_password" className="mb-1 block text-sm font-medium">Current Password</label>
          <input
            id="current_password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
        </div>
        <div>
          <label htmlFor="new_password" className="mb-1 block text-sm font-medium">New Password</label>
          <input
            id="new_password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
        </div>
        <div>
          <label htmlFor="confirm_password" className="mb-1 block text-sm font-medium">Confirm Password</label>
          <input
            id="confirm_password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800"
          />
        </div>

        <button
          type="submit"
          disabled={changePassword.isPending}
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          {changePassword.isPending ? "Updating..." : "Update Password"}
        </button>
      </form>
    </div>
  );
}
