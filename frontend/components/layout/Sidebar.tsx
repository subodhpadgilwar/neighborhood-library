"use client";

import {
  ArrowLeftRight,
  BookOpen,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Users,
  Users2,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { ChangePasswordModal } from "@/components/staff/ChangePasswordModal";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/authContext";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/books", label: "Books", icon: BookOpen },
  { href: "/members", label: "Members", icon: Users },
  { href: "/lending", label: "Lending", icon: ArrowLeftRight },
  { href: "/staff", label: "Staff", icon: Users2 },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();
  const { staff, logout } = useAuth();
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border bg-card">
        <div className="flex h-14 items-center gap-2 border-b border-border px-4">
          <BookOpen className="size-5 shrink-0 text-primary" aria-hidden />
          <span className="truncate font-semibold tracking-tight">
            Neighborhood Library
          </span>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon className="size-4 shrink-0" aria-hidden />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3">
          <Separator className="mb-3" />
          <div className="mb-3 space-y-0.5 px-1">
            <p className="truncate text-sm font-medium">
              {staff?.full_name ?? "Staff"}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {staff?.email ?? ""}
            </p>
          </div>
          <div className="space-y-2">
            <Button
              type="button"
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={() => setIsChangePasswordOpen(true)}
            >
              <KeyRound className="size-4" aria-hidden />
              Change Password
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={logout}
            >
              <LogOut className="size-4" aria-hidden />
              Log out
            </Button>
          </div>
        </div>
      </aside>

      <ChangePasswordModal
        isOpen={isChangePasswordOpen}
        onClose={() => setIsChangePasswordOpen(false)}
        mode="own"
      />
    </>
  );
}
