import {
  differenceInCalendarDays,
  format,
  parseISO,
  startOfDay,
} from "date-fns";

function parseDate(dateStr: string): Date {
  return startOfDay(parseISO(dateStr));
}

export function formatDate(dateStr: string): string {
  return format(parseISO(dateStr), "d MMM yyyy");
}

export function formatDateTime(dateStr: string): string {
  return format(parseISO(dateStr), "d MMM yyyy, h:mm a");
}

export function daysUntilDue(dueDateStr: string): number {
  const due = parseDate(dueDateStr);
  const today = startOfDay(new Date());
  return differenceInCalendarDays(due, today);
}

export function isDueSoon(dueDateStr: string): boolean {
  const days = daysUntilDue(dueDateStr);
  return days >= 0 && days <= 3;
}

export function daysOverdue(dueDateStr: string): number {
  const due = parseDate(dueDateStr);
  const today = startOfDay(new Date());
  return Math.max(0, differenceInCalendarDays(today, due));
}
