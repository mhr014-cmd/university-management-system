"""
Unit tests: app.middleware.error_handlers._sanitize_validation_errors.

V1.1 stabilization fix: a validation error's `input` echo must never
contain a raw submitted password (CLAUDE.md §12/§13) — this is the actual
mechanism that stops the leak, since Pydantic v2 always echoes the raw
pre-validation input regardless of the field's declared type (SecretStr
does not suppress this on its own).
"""

from app.middleware.error_handlers import _sanitize_validation_errors
from app.schemas.auth import LoginRequest, PasswordChangeRequest
from app.schemas.student import StudentCreate
from app.schemas.teacher import TeacherCreate
from pydantic import ValidationError


def _errors_for(model_cls, **kwargs) -> list[dict]:
    try:
        model_cls(**kwargs)
    except ValidationError as exc:
        return exc.errors()
    raise AssertionError("expected a ValidationError")


class TestFieldLevelRedaction:
    def test_login_password_redacted(self):
        errors = _sanitize_validation_errors(_errors_for(LoginRequest, email="a@example.com", password=""))
        assert errors[0]["loc"] == ("password",)
        assert errors[0]["input"] == "[REDACTED]"

    def test_password_change_new_password_redacted(self):
        errors = _sanitize_validation_errors(
            _errors_for(PasswordChangeRequest, current_password="whatever", new_password="short")
        )
        assert errors[0]["loc"] == ("new_password",)
        assert errors[0]["input"] == "[REDACTED]"

    def test_student_create_password_redacted(self):
        errors = _sanitize_validation_errors(
            _errors_for(
                StudentCreate,
                email="a@example.com",
                password="short",
                first_name="A",
                last_name="B",
                department_id="11111111-1111-1111-1111-111111111111",
                enrollment_date="2026-01-01",
            )
        )
        password_errors = [e for e in errors if e["loc"] == ("password",)]
        assert password_errors, "expected a password field error"
        assert password_errors[0]["input"] == "[REDACTED]"

    def test_teacher_create_password_redacted(self):
        errors = _sanitize_validation_errors(
            _errors_for(
                TeacherCreate,
                email="a@example.com",
                password="short",
                first_name="A",
                last_name="B",
                department_id="11111111-1111-1111-1111-111111111111",
            )
        )
        password_errors = [e for e in errors if e["loc"] == ("password",)]
        assert password_errors, "expected a password field error"
        assert password_errors[0]["input"] == "[REDACTED]"

    def test_non_sensitive_field_left_untouched(self):
        errors = _sanitize_validation_errors(_errors_for(LoginRequest, email="not-an-email", password="a-real-value"))
        email_errors = [e for e in errors if e["loc"] == ("email",)]
        assert email_errors[0]["input"] == "not-an-email"


class TestWholeModelRedaction:
    def test_password_differ_validator_redacts_both_fields_in_input_dict(self):
        errors = _sanitize_validation_errors(
            _errors_for(PasswordChangeRequest, current_password="same-password-123", new_password="same-password-123")
        )
        assert errors[0]["loc"] == ()
        assert errors[0]["input"] == {"current_password": "[REDACTED]", "new_password": "[REDACTED]"}
