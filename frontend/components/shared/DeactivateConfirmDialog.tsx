"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
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

type ApiClientError = { status: string; message: string };

interface DeactivateConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  entityType: "book" | "member";
  entityName: string;
  id: string;
  onConfirm: (id: string) => Promise<unknown>;
}

function getMessage(entityType: "book" | "member", entityName: string): string {
  if (entityType === "book") {
    return `Are you sure you want to deactivate '${entityName}'? It will no longer appear in the available books list and cannot be borrowed.`;
  }
  return `Are you sure you want to deactivate '${entityName}'? They will no longer be able to borrow books. This will fail if they have active loans.`;
}

function getEntityLabel(entityType: "book" | "member"): string {
  return entityType === "book" ? "Book" : "Member";
}

export function DeactivateConfirmDialog({
  isOpen,
  onClose,
  onSuccess,
  entityType,
  entityName,
  id,
  onConfirm,
}: DeactivateConfirmDialogProps) {
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setApiError(null);
    }
  }, [isOpen, id]);

  async function handleDeactivate() {
    if (!id) {
      return;
    }

    setIsSubmitting(true);
    setApiError(null);

    try {
      await onConfirm(id);
      toast.success(`${entityName} deactivated`);
      onClose();
      onSuccess();
    } catch (err) {
      const error = err as ApiClientError;
      setApiError(
        typeof error?.message === "string"
          ? error.message
          : "Failed to deactivate.",
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
          setApiError(null);
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mb-2 flex justify-center">
            <div className="flex size-10 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle
                className="size-5 text-destructive"
                aria-hidden
              />
            </div>
          </div>
          <DialogTitle className="text-center">
            Deactivate {getEntityLabel(entityType)}?
          </DialogTitle>
          <DialogDescription className="text-center">
            {getMessage(entityType, entityName)}
          </DialogDescription>
        </DialogHeader>

        {apiError ? (
          <p role="alert" className="text-sm text-destructive">
            {apiError}
          </p>
        ) : null}

        <DialogFooter className="sm:justify-center">
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
            disabled={isSubmitting || !id}
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
