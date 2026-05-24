"use client";

import { Loader2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { formatLoanDate } from "@/components/lending/loanUtils";
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
import { Separator } from "@/components/ui/separator";
import {
  dateInputToApiIso,
  formatDate,
  isoToDateInputValue,
  isCalendarDayBefore,
} from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import { lendingService } from "@/services";
import type { Lending } from "@/types";

type ApiClientError = { status: string; message: string };

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
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setDueDateInput(isoToDateInputValue(lending.due_date));
    setFieldError(null);
    setApiError(null);
  }, [isOpen, lending]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldError(null);
    setApiError(null);

    if (!dueDateInput) {
      setFieldError("Please select a due date.");
      return;
    }

    if (isCalendarDayBefore(dueDateInput, borrowDateInput)) {
      setFieldError("Due date cannot be before the borrow date.");
      return;
    }

    setIsSubmitting(true);
    try {
      await lendingService.updateDueDate(
        lending.id,
        dateInputToApiIso(dueDateInput),
      );
      toast.success("Due date updated successfully");
      onClose();
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Failed to update due date.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Update Due Date</DialogTitle>
          <DialogDescription>
            Adjust when this loan must be returned.
          </DialogDescription>
        </DialogHeader>

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

        <form onSubmit={handleSubmit} className="space-y-4">
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
                setApiError(null);
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

          {apiError ? (
            <p role="alert" className="text-sm text-destructive">
              {apiError}
            </p>
          ) : null}

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
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
              ) : (
                "Update Due Date"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
