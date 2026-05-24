import {
  addDays,
  differenceInCalendarDays,
  format,
  isBefore,
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

export function defaultDueDateFromToday(days = 14): Date {
  return addDays(startOfDay(new Date()), days);
}

export function formatDateInputValue(date: Date): string {
  return format(date, "yyyy-MM-dd");
}

export function isoToDateInputValue(iso: string): string {
  return formatDateInputValue(parseISO(iso));
}

export function isCalendarDayBefore(
  candidateInput: string,
  referenceInput: string,
): boolean {
  return isBefore(
    startOfDay(parseISO(candidateInput)),
    startOfDay(parseISO(referenceInput)),
  );
}

/** Converts YYYY-MM-DD from a date input to an ISO string for the API. */
export function dateInputToApiIso(dateInput: string): string {
  const [year, month, day] = dateInput.split("-").map(Number);
  return new Date(year, month - 1, day, 23, 59, 59, 999).toISOString();
}
