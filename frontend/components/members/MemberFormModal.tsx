"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { memberService } from "@/services";
import type { Member, MemberCreate, MemberUpdate } from "@/types";

type ApiClientError = {
  status: string;
  message: string;
};

interface MemberFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member?: Member | null;
  onSuccess: () => void;
}

interface FormState {
  name: string;
  email: string;
  phone: string;
  address: string;
}

const emptyForm: FormState = {
  name: "",
  email: "",
  phone: "",
  address: "",
};

function memberToForm(member: Member): FormState {
  return {
    name: member.name,
    email: member.email,
    phone: member.phone ?? "",
    address: member.address ?? "",
  };
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

function isValidPhone(phone: string): boolean {
  if (!phone.trim()) {
    return true;
  }
  const digits = phone.replace(/\D/g, "");
  return /^\d{10,15}$/.test(digits);
}

export function MemberFormModal({
  open,
  onOpenChange,
  member,
  onSuccess,
}: MemberFormModalProps) {
  const isEdit = member != null;
  const [form, setForm] = useState<FormState>(emptyForm);
  const [fieldErrors, setFieldErrors] = useState<Partial<FormState>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!open) {
      return;
    }
    setForm(member ? memberToForm(member) : emptyForm);
    setFieldErrors({});
    setApiError(null);
  }, [open, member]);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
    setApiError(null);
  }

  function validate(): boolean {
    const errors: Partial<FormState> = {};
    if (!form.name.trim()) {
      errors.name = "Name is required";
    }
    if (!form.email.trim()) {
      errors.email = "Email is required";
    } else if (!isValidEmail(form.email)) {
      errors.email = "Enter a valid email address";
    }
    if (!isValidPhone(form.phone)) {
      errors.phone = "Phone must contain 10–15 digits";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validate()) {
      return;
    }

    const payload = {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || undefined,
      address: form.address.trim() || undefined,
    };

    setIsSubmitting(true);
    setApiError(null);

    try {
      if (isEdit && member) {
        await memberService.update(member.id, payload as MemberUpdate);
        toast.success("Member updated successfully");
      } else {
        await memberService.create(payload as MemberCreate);
        toast.success("Member registered successfully");
      }
      setForm(emptyForm);
      setFieldErrors({});
      onOpenChange(false);
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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit Member" : "Register Member"}
          </DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update member contact details."
              : "Add a new library member."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="member-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="member-name"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.name)}
            />
            {fieldErrors.name ? (
              <p className="text-xs text-destructive">{fieldErrors.name}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="member-email">
              Email <span className="text-destructive">*</span>
            </Label>
            <Input
              id="member-email"
              type="email"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.email)}
            />
            {fieldErrors.email ? (
              <p className="text-xs text-destructive">{fieldErrors.email}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="member-phone">Phone</Label>
            <Input
              id="member-phone"
              type="tel"
              value={form.phone}
              onChange={(e) => updateField("phone", e.target.value)}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.phone)}
            />
            <p className="text-xs text-muted-foreground">10-15 digits</p>
            {fieldErrors.phone ? (
              <p className="text-xs text-destructive">{fieldErrors.phone}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="member-address">Address</Label>
            <Input
              id="member-address"
              value={form.address}
              onChange={(e) => updateField("address", e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {apiError ? (
            <p role="alert" className="text-sm text-destructive">
              {apiError}
            </p>
          ) : null}

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Loading...
                </>
              ) : isEdit ? (
                "Save Changes"
              ) : (
                "Register"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
