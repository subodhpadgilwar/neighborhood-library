"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export interface ErrorFallbackProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export function ErrorFallback({ error, reset }: ErrorFallbackProps) {
  useEffect(() => {
    console.error("Unhandled application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h2 className="text-xl font-semibold text-destructive">
        Something went wrong
      </h2>
      <p className="max-w-md text-center text-sm text-muted-foreground">
        {error.message || "An unexpected error occurred. Please try again."}
      </p>
      <Button onClick={reset} variant="outline">
        Try again
      </Button>
    </div>
  );
}

