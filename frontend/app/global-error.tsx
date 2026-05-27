"use client";

import { ErrorFallback, type ErrorFallbackProps } from "@/components/shared/ErrorFallback";

export default function GlobalError(props: ErrorFallbackProps) {
  return (
    <html lang="en">
      <body>
        <ErrorFallback {...props} />
      </body>
    </html>
  );
}

