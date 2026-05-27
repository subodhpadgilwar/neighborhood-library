"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { formatLoanDate } from "@/components/lending/loanUtils";
import { FormDialog } from "@/components/shared/FormDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  dateInputToApiIso,
  formatDate,
  isoToDateInputValue,
  isCalendarDayBefore,
} from "@/lib/dateUtils";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { useFormSubmitState } from "@/hooks/useFormSubmitState";
import { cn } from "@/lib/utils";
import { lendingService } from "@/services";
import type { Lending } from "@/types";

interface UpdateDueDateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  lending: Lending;
}

export function UpdateDueDateModal({
  isOpen,
  onClose,
  onSuccess,
  lending,
}: UpdateDueDateModalProps) {
  const borrowDateInput = isoToDateInputValue(lending.borrowed_at);
  const [dueDateInput, setDueDateInput] = useState(
    isoToDateInputValue(lending.due_date),
  );
  const [fieldError, setFieldError] = useState<string | null>(null);
  const { isSubmitting, apiError, clearApiError, runSubmit } =
    useFormSubmitState();

  useDeferredEffect(() => {
    if (!isOpen) {
      return;
    }
    setDueDateInput(isoToDateInputValue(lending.due_date));
    setFieldError(null);
    clearApiError();
  }, [isOpen, lending]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldError(null);
    clearApiError();

    if (!dueDateInput) {
      setFieldError("Please select a due date.");
      return;
    }

    if (isCalendarDayBefore(dueDateInput, borrowDateInput)) {
      setFieldError("Due date cannot be before the borrow date.");
      return;
    }

    const result = await runSubmit(async () => {
      await lendingService.updateDueDate(
        lending.id,
        dateInputToApiIso(dueDateInput),
      );
      toast.success("Due date updated successfully");
      onClose();
      onSuccess();
      return true;
    }, "Failed to update due date.");

    if (!result) return;
  }

  return (
    <FormDialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      title="Update Due Date"
      description="Adjust when this loan must be returned."
      submitLabel="Update Due Date"
      isSubmitting={isSubmitting}
      apiError={apiError}
      onSubmit={handleSubmit}
      className="sm:max-w-md"
    >
      <div className="space-y-1 rounded-lg bg-muted/50 p-3 text-sm">
        <p>
          <span className="text-muted-foreground">Book:</span>{" "}
          {lending.book_title}
        </p>
        <p>
          <span className="text-muted-foreground">Member:</span>{" "}
          {lending.member_name}
        </p>
        <p>
          <span className="text-muted-foreground">Borrowed:</span>{" "}
          {formatLoanDate(lending.borrowed_at)}
        </p>
        <p>
          <span className="text-muted-foreground">Current Due:</span>{" "}
          {formatLoanDate(lending.due_date)}
        </p>
      </div>

      <Separator />

      <div className="space-y-2">
        <Label htmlFor="new-due-date">New Due Date</Label>
        <Input
          id="new-due-date"
          type="date"
          min={borrowDateInput}
          value={dueDateInput}
          onChange={(e) => {
            setDueDateInput(e.target.value);
            setFieldError(null);
            clearApiError();
          }}
          disabled={isSubmitting}
          className={cn(
            "w-full",
            "[&::-webkit-calendar-picker-indicator]:cursor-pointer",
          )}
          aria-invalid={Boolean(fieldError)}
        />
        <p className="text-xs text-muted-foreground">
          Due date must be on or after the borrow date (
          {formatDate(lending.borrowed_at)}).
        </p>
        {fieldError ? (
          <p className="text-xs text-destructive">{fieldError}</p>
        ) : null}
      </div>
    </FormDialog>
  );
}
