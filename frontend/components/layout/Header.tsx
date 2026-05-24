"use client";

import { useAuth } from "@/lib/authContext";

function getInitials(fullName: string): string {
  return fullName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { staff } = useAuth();
  const initials = staff ? getInitials(staff.full_name) : "?";

  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-6">
      <h1 className="text-lg font-semibold tracking-tight">{title}</h1>

      <div className="flex items-center gap-3">
        <span className="hidden text-sm text-muted-foreground sm:inline">
          {staff?.full_name}
        </span>
        <div
          className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary"
          aria-hidden
        >
          {initials}
        </div>
      </div>
    </header>
  );
}
