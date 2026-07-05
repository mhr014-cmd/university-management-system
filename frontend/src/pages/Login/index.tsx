// Login page (FR-001, FR-005). Layout and validation behavior match
// docs/UI_Wireframes.md Section 1: inline validation on blur, a single
// error banner for server-side failures (not tied to a specific field),
// redirect to /dashboard on success.
//
// Production-polish pass: visual redesign only (spacing, typography,
// hierarchy, dark-mode contrast, show/hide password toggle) — the
// validation rules, error messages, and submit/redirect behavior below
// are unchanged from the pre-polish version.

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";
import { AlertCircle, GraduationCap } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";
import { Button } from "../../components/ui/Button";
import { PasswordInput } from "../../components/ui/PasswordInput";
import { errorTextClass, inputClass, labelClass } from "../../components/ui/classNames";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailTouched, setEmailTouched] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const emailError = emailTouched && !EMAIL_PATTERN.test(email) ? "Enter a valid email address." : null;
  const passwordError = passwordTouched && password.length === 0 ? "Password is required." : null;
  const canSubmit = EMAIL_PATTERN.test(email) && password.length > 0 && !isSubmitting;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setEmailTouched(true);
    setPasswordTouched(true);
    if (!EMAIL_PATTERN.test(email) || password.length === 0) return;

    setServerError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      if (isAxiosError(error) && error.response) {
        const status = error.response.status;
        if (status === 401) {
          setServerError("Incorrect email or password.");
        } else if (status === 403) {
          setServerError("This account has been deactivated.");
        } else {
          setServerError("Something went wrong. Please try again.");
        }
      } else {
        setServerError("Could not reach the server. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900">
            <GraduationCap className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            ICT Education
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Sign in to your account to continue</p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {serverError && (
            <div
              role="alert"
              className="mb-5 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/50 dark:text-red-300"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <div>
              <label htmlFor="email" className={labelClass}>
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => setEmailTouched(true)}
                className={inputClass}
                autoComplete="email"
                autoFocus
                aria-invalid={!!emailError}
                aria-describedby={emailError ? "email-error" : undefined}
                placeholder="you@example.com"
              />
              {emailError && (
                <p id="email-error" className={errorTextClass}>
                  {emailError}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className={labelClass}>
                Password
              </label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => setPasswordTouched(true)}
                autoComplete="current-password"
                aria-invalid={!!passwordError}
                aria-describedby={passwordError ? "password-error" : undefined}
                placeholder="••••••••"
              />
              {passwordError && (
                <p id="password-error" className={errorTextClass}>
                  {passwordError}
                </p>
              )}
            </div>

            <Button
              type="submit"
              disabled={!canSubmit}
              isLoading={isSubmitting}
              className="w-full"
              aria-busy={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Log In"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
