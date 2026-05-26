"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { FormDialog } from "@/components/shared/FormDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { isValidEmail, isValidPassword, PASSWORD_HINT } from "@/lib/password";
import { staffService } from "@/services";
import type { Staff, StaffCreate, StaffRole, StaffUpdate } from "@/types";

type ApiClientError = { status: string; message: string };

interface StaffFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  mode: "create" | "edit";
  initialData?: Staff | null;
}

interface FormState {
  full_name: string;
  email: string;
  role: StaffRole;
  password: string;
  confirm_password: string;
}

const emptyForm: FormState = {
  full_name: "",
  email: "",
  role: "staff",
  password: "",
  confirm_password: "",
};

function staffToForm(staff: Staff): FormState {
  return {
    full_name: staff.full_name,
    email: staff.email,
    role: staff.role,
    password: "",
    confirm_password: "",
  };
}

function PasswordField({
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

export function StaffFormModal({
  isOpen,
  onClose,
  onSuccess,
  mode,
  initialData,
}: StaffFormModalProps) {
  const isCreate = mode === "create";
  const [form, setForm] = useState<FormState>(emptyForm);
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useDeferredEffect(() => {
    if (!isOpen) {
      return;
    }
    setForm(
      !isCreate && initialData ? staffToForm(initialData) : emptyForm,
    );
    setFieldErrors({});
    setApiError(null);
  }, [isOpen, isCreate, initialData]);

  function validate(): boolean {
    const errors: Partial<FormState> = {};
    if (!form.full_name.trim()) {
      errors.full_name = "Full name is required";
    }
    if (!form.email.trim()) {
      errors.email = "Email is required";
    } else if (!isValidEmail(form.email)) {
      errors.email = "Enter a valid email address";
    }
    if (isCreate) {
      if (!form.password) {
        errors.password = "Password is required";
      } else if (!isValidPassword(form.password)) {
        errors.password = "Password does not meet requirements";
      }
      if (!form.confirm_password) {
        errors.confirm_password = "Please confirm your password";
      } else if (form.password !== form.confirm_password) {
        errors.confirm_password = "Passwords do not match";
      }
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
      if (isCreate) {
        const payload: StaffCreate = {
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          role: form.role,
          password: form.password,
        };
        await staffService.create(payload);
        toast.success("Staff member added successfully");
      } else if (initialData) {
        const payload: StaffUpdate = {
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          role: form.role,
        };
        await staffService.update(initialData.id, payload);
        toast.success("Staff member updated successfully");
      }
      setForm(emptyForm);
      setFieldErrors({});
      onClose();
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <FormDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
      title={isCreate ? "Add Staff Member" : "Edit Staff Member"}
      description={
        isCreate
          ? "Create a new staff account with login credentials."
          : "Update staff profile details."
      }
      submitLabel={isCreate ? "Add Staff" : "Save Changes"}
      isSubmitting={isSubmitting}
      apiError={apiError}
      onSubmit={handleSubmit}
    >
          <div className="space-y-2">
            <Label htmlFor="staff-full-name">
              Full Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="staff-full-name"
              value={form.full_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, full_name: e.target.value }))
              }
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.full_name)}
            />
            {fieldErrors.full_name ? (
              <p className="text-xs text-destructive">{fieldErrors.full_name}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="staff-email">
              Email <span className="text-destructive">*</span>
            </Label>
            <Input
              id="staff-email"
              type="email"
              value={form.email}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, email: e.target.value }))
              }
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.email)}
            />
            {fieldErrors.email ? (
              <p className="text-xs text-destructive">{fieldErrors.email}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="staff-role">Role</Label>
            <Select
              value={form.role}
              onValueChange={(role) =>
                setForm((prev) => ({ ...prev, role: role as StaffRole }))
              }
              disabled={isSubmitting || initialData?.is_default_admin}
            >
              <SelectTrigger id="staff-role" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="staff">Staff</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isCreate ? (
            <>
              <PasswordField
                id="staff-password"
                label="Password *"
                value={form.password}
                onChange={(password) =>
                  setForm((prev) => ({ ...prev, password }))
                }
                disabled={isSubmitting}
                error={fieldErrors.password}
              />
              <p className="-mt-2 text-xs text-muted-foreground">
                {PASSWORD_HINT}
              </p>
              <PasswordField
                id="staff-confirm-password"
                label="Confirm Password *"
                value={form.confirm_password}
                onChange={(confirm_password) =>
                  setForm((prev) => ({ ...prev, confirm_password }))
                }
                disabled={isSubmitting}
                error={fieldErrors.confirm_password}
              />
            </>
          ) : null}

    </FormDialog>
  );
}
