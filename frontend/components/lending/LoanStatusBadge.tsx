"use client";

import { Badge } from "@/components/ui/badge";
import type { LoanStatus } from "@/components/lending/loanUtils";

export function LoanStatusBadge({ status }: { status: LoanStatus }) {
  if (status === "overdue") {
    return (
      <Badge
        variant="destructive"
        className="bg-destructive/15 text-destructive hover:bg-destructive/15"
      >
        Overdue
      </Badge>
    );
  }
  if (status === "due-soon") {
    return (
      <Badge className="border-amber-200 bg-amber-100 text-amber-800 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
        Due Soon
      </Badge>
    );
  }
  return (
    <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
      Active
    </Badge>
  );
}
