import { isDueSoon } from "@/lib/dateUtils";
import type { Lending } from "@/types";

export type LoanStatus = "overdue" | "due-soon" | "active";

export function getLoanStatus(lending: Lending): LoanStatus {
  if (lending.is_overdue) {
    return "overdue";
  }
  if (isDueSoon(lending.due_date)) {
    return "due-soon";
  }
  return "active";
}

export { formatDate as formatLoanDate, daysOverdue } from "@/lib/dateUtils";
