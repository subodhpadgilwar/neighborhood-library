"use client";

import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface ConfirmPopoverProps {
  message: string;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  children: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  isLoading?: boolean;
  confirmLabel?: string;
  cancelLabel?: string;
}

export function ConfirmPopover({
  message,
  onConfirm,
  onCancel,
  children,
  open,
  onOpenChange,
  isLoading = false,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
}: ConfirmPopoverProps) {
  function handleCancel() {
    onCancel?.();
    onOpenChange?.(false);
  }

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent className="w-56" align="end">
        <p className="mb-3 text-sm">{message}</p>
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={isLoading}
            onClick={() => void onConfirm()}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" />
                Loading...
              </>
            ) : (
              confirmLabel
            )}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
