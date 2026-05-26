"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-full flex-1 items-center justify-center bg-muted/40 px-4 py-12">
      <section className="w-full max-w-md rounded-lg border bg-card p-6 text-center">
        <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <AlertTriangle className="size-6" aria-hidden />
        </div>
        <h1 className="text-xl font-semibold tracking-tight">
          Something went wrong
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The page hit an unexpected error. You can retry without leaving the
          app.
        </p>
        <Button type="button" onClick={reset} className="mt-6 gap-2">
          <RefreshCw className="size-4" aria-hidden />
          Try Again
        </Button>
      </section>
    </main>
  );
}
