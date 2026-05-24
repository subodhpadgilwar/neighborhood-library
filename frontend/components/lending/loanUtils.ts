import {
  differenceInCalendarDays,
  format,
  parseISO,
  startOfDay,
} from "date-fns";

import type { Lending } from "@/types";

export type LoanStatus = "overdue" | "due-soon" | "active";

export function getLoanStatus(lending: Lending): LoanStatus {
  if (lending.is_overdue) {
    return "overdue";
  }
  const due = startOfDay(parseISO(lending.due_date));
  const today = startOfDay(new Date());
  const daysUntilDue = differenceInCalendarDays(due, today);
  if (daysUntilDue >= 0 && daysUntilDue <= 3) {
    return "due-soon";
  }
  return "active";
}

export function formatLoanDate(iso: string): string {
  return format(parseISO(iso), "MMM d, yyyy");
}

export function getDaysOverdue(dueDate: string): number {
  const due = startOfDay(parseISO(dueDate));
  const today = startOfDay(new Date());
  return Math.max(0, differenceInCalendarDays(today, due));
}
