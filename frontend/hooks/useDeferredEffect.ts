"use client";

import { useEffect, type DependencyList } from "react";

export function useDeferredEffect(
  callback: () => void | (() => void),
  dependencies: DependencyList,
) {
  useEffect(() => {
    let cleanup: void | (() => void);
    const timeoutId = window.setTimeout(() => {
      cleanup = callback();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
      cleanup?.();
    };
    // This hook intentionally mirrors useEffect's dependency API for callers.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
}
