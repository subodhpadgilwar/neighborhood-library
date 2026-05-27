"use client";

import { ErrorFallback } from "@/components/shared/ErrorFallback";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return <ErrorFallback error={error} reset={reset} />;
}
