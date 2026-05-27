import { useCallback, useState } from "react";

type ApiClientError = {
  message?: string;
};

/**
 * Shared submit/loading/error state for form dialogs.
 * Keeps modal submit behavior consistent across create/edit flows.
 */
export function useFormSubmitState() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const clearApiError = useCallback(() => {
    setApiError(null);
  }, []);

  const runSubmit = useCallback(
    async <T>(action: () => Promise<T>, fallbackMessage: string): Promise<T | null> => {
      setIsSubmitting(true);
      setApiError(null);
      try {
        return await action();
      } catch (err) {
        const error = err as ApiClientError;
        setApiError(
          typeof error?.message === "string" ? error.message : fallbackMessage,
        );
        return null;
      } finally {
        setIsSubmitting(false);
      }
    },
    [],
  );

  return {
    isSubmitting,
    apiError,
    setApiError,
    clearApiError,
    runSubmit,
  };
}

