"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
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
import { staffService } from "@/services";
import type { Staff } from "@/types";

type ApiClientError = { status: string; message: string };

interface DeactivateConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  staff: Staff | null;
}

export function DeactivateConfirmDialog({
  isOpen,
  onClose,
  onSuccess,
  staff,
}: DeactivateConfirmDialogProps) {
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleDeactivate() {
    if (!staff) {
      return;
    }

    setIsSubmitting(true);
    setApiError(null);

    try {
      await staffService.deactivate(staff.id);
      toast.success(`${staff.full_name} has been deactivated`);
      onClose();
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      const message =
        typeof error?.message === "string"
          ? error.message
          : "Failed to deactivate staff member.";
      setApiError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          setApiError(null);
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Deactivate staff member</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-3 pt-1">
              <p className="text-base font-medium text-foreground">
                {staff?.full_name}
              </p>
              <p>
                Are you sure you want to deactivate {staff?.full_name}? They
                will lose access to the system immediately.
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>

        {apiError ? (
          <p role="alert" className="text-sm text-destructive">
            {apiError}
          </p>
        ) : null}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={isSubmitting}
            onClick={() => void handleDeactivate()}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin" />
                Loading...
              </>
            ) : (
              "Deactivate"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
