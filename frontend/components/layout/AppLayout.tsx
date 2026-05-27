"use client";

import type { ReactNode } from "react";

import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/authContext";

interface AppLayoutProps {
  children: ReactNode;
  title: string;
}

export function AppLayout({ children, title }: AppLayoutProps) {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <div className="h-14 w-full border-b bg-background px-4 flex items-center gap-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="ml-auto h-8 w-8 rounded-full" />
        </div>
        <div className="flex flex-1">
          <div className="hidden w-56 shrink-0 border-r bg-background md:flex flex-col gap-2 p-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full rounded-md" />
            ))}
          </div>
          <main className="flex-1 p-6">
            <Skeleton className="h-8 w-64 mb-4" />
            <Skeleton className="h-64 w-full rounded-lg" />
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-1">
      <Sidebar />
      <div className="flex min-h-full flex-1 flex-col pl-64">
        <Header title={title} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
