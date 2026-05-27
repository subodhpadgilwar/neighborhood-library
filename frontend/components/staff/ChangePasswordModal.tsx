"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { FormDialog } from "@/components/shared/FormDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { isValidPassword, PASSWORD_HINT } from "@/lib/password";
import { staffService } from "@/services";
import type { Staff } from "@/types";

type ApiClientError = { status: string; message: string };

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: "own" | "admin";
  targetStaff?: Staff | null;
}

interface FormState {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

const emptyForm: FormState = {
  current_password: "",
  new_password: "",
  confirm_password: "",
};

function PasswordInput({
  id,
  label,
  value,
  onChange,
  disabled,
  error,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          id={id}
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="pr-10"
          aria-invalid={Boolean(error)}
        />
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="absolute top-1/2 right-1 -translate-y-1/2"
          onClick={() => setShow((s) => !s)}
          disabled={disabled}
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </Button>
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

export function ChangePasswordModal({
  isOpen,
  onClose,
  mode,
  targetStaff,
}: ChangePasswordModalProps) {
  const isOwn = mode === "own";
  const [form, setForm] = useState<FormState>(emptyForm);
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useDeferredEffect(() => {
    if (!isOpen) {
      return;
    }
    setForm(emptyForm);
    setFieldErrors({});
    setApiError(null);
  }, [isOpen]);

  function validate(): boolean {
    const errors: Partial<FormState> = {};
    if (isOwn && !form.current_password) {
      errors.current_password = "Current password is required";
    }
    if (!form.new_password) {
      errors.new_password = "New password is required";
    } else if (!isValidPassword(form.new_password)) {
      errors.new_password = "Password does not meet requirements";
    }
    if (!form.confirm_password) {
      errors.confirm_password = "Please confirm your new password";
    } else if (form.new_password !== form.confirm_password) {
      errors.confirm_password = "Passwords do not match";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    setApiError(null);

    try {
      if (isOwn) {
        await staffService.changeOwnPassword({
          current_password: form.current_password,
          new_password: form.new_password,
          confirm_password: form.confirm_password,
        });
        toast.success("Password changed successfully");
      } else if (targetStaff) {
        await staffService.adminChangePassword(targetStaff.id, {
          new_password: form.new_password,
          confirm_password: form.confirm_password,
        });
        toast.success(`Password updated for ${targetStaff.full_name}`);
      }
      setForm(emptyForm);
      onClose();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Failed to change password.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <FormDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      title="Change Password"
      description={
        isOwn
          ? "Enter your current password and choose a new one."
          : `You are changing the password for ${targetStaff?.full_name ?? "this staff member"}.`
      }
      submitLabel="Update Password"
      isSubmitting={isSubmitting}
      apiError={apiError}
      onSubmit={handleSubmit}
    >
      {isOwn ? (
        <PasswordInput
          id="current-password"
          label="Current Password *"
          value={form.current_password}
          onChange={(current_password) =>
            setForm((prev) => ({ ...prev, current_password }))
          }
          disabled={isSubmitting}
          error={fieldErrors.current_password}
        />
      ) : null}

      <PasswordInput
        id="new-password"
        label="New Password *"
        value={form.new_password}
        onChange={(new_password) =>
          setForm((prev) => ({ ...prev, new_password }))
        }
        disabled={isSubmitting}
        error={fieldErrors.new_password}
      />
      <p className="-mt-2 text-xs text-muted-foreground">{PASSWORD_HINT}</p>

      <PasswordInput
        id="confirm-new-password"
        label="Confirm New Password *"
        value={form.confirm_password}
        onChange={(confirm_password) =>
          setForm((prev) => ({ ...prev, confirm_password }))
        }
        disabled={isSubmitting}
        error={fieldErrors.confirm_password}
      />
    </FormDialog>
  );
}
