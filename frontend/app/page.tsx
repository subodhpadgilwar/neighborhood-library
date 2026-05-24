"use client";

import {
  AlertCircle,
  AlertTriangle,
  ArrowLeftRight,
  BookOpen,
  Plus,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { GenrePieChart } from "@/components/analytics/GenrePieChart";
import { MonthlyLendingChart } from "@/components/analytics/MonthlyLendingChart";
import { TopBooksChart } from "@/components/analytics/TopBooksChart";
import { AppLayout } from "@/components/layout/AppLayout";
import { getLoanStatus } from "@/components/lending/loanUtils";
import { LoanStatusBadge } from "@/components/lending/LoanStatusBadge";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDate } from "@/lib/dateUtils";
import { cn } from "@/lib/utils";
import { analyticsService, lendingService } from "@/services";
import type { Lending, SummaryStats } from "@/types";

interface DashboardData {
  summary: SummaryStats | null;
  recentLoans: Lending[];
}

interface StatCardProps {
  label: string;
  value: number | string;
  subText?: string;
  accent: "blue" | "green" | "orange" | "red";
  pulse?: boolean;
  ringPulse?: boolean;
  icon: ReactNode;
}

const accentStyles = {
  blue: "border-l-blue-500 bg-blue-50/60 dark:bg-blue-950/30",
  green: "border-l-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/30",
  orange: "border-l-orange-500 bg-orange-50/60 dark:bg-orange-950/30",
  red: "border-l-red-500 bg-red-50/60 dark:bg-red-950/30",
} as const;

function StatCard({
  label,
  value,
  subText,
  accent,
  pulse,
  ringPulse,
  icon,
}: StatCardProps) {
  return (
    <Card
      className={cn(
        "border-l-4 py-4 shadow-none",
        accentStyles[accent],
        pulse && "animate-pulse",
        ringPulse && "ring-2 ring-red-400/70 ring-offset-2 dark:ring-red-500/50",
      )}
    >
      <CardContent className="flex items-start justify-between px-4 py-0">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-3xl font-semibold tracking-tight tabular-nums">
            {value}
          </p>
          {subText ? (
            <p className="mt-1 text-xs text-muted-foreground">{subText}</p>
          ) : null}
        </div>
        <div className="text-muted-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}

function StatsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i} className="py-4">
          <CardContent className="space-y-2 px-4 py-0">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-9 w-16" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);

      const results = await Promise.allSettled([
        analyticsService.getSummary(),
        lendingService.getHistory({
          limit: 5,
          sort_by: "borrowed_at",
          sort_order: "desc",
        }),
      ]);

      if (cancelled) {
        return;
      }

      const labels = ["summary", "recent activity"];
      const errors: string[] = [];

      const summary =
        results[0].status === "fulfilled" ? results[0].value : null;
      const historyResult =
        results[1].status === "fulfilled" ? results[1].value : null;

      results.forEach((result, index) => {
        if (result.status === "rejected") {
          errors.push(`Failed to load ${labels[index]}`);
        }
      });

      if (errors.length > 0) {
        setError(errors.join(". ") + ".");
      }

      setData({
        summary,
        recentLoans: historyResult?.items ?? [],
      });
      setIsLoading(false);
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  const summary = data?.summary;
  const overdueCount = summary?.overdue_loans ?? 0;
  const showBanner = !bannerDismissed && !isLoading && overdueCount > 0;

  const overdueMessage = `${overdueCount} book(s) are overdue and need attention`;

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6">
        {error ? (
          <ErrorMessage message={`${error} Some figures may be incomplete.`} />
        ) : null}

        {showBanner ? (
          <div className="flex items-start gap-3 rounded-lg border border-amber-300/80 bg-amber-50 px-4 py-3 text-amber-950 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-100">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" aria-hidden />
            <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-medium">{overdueMessage}</p>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" asChild>
                  <Link href="/lending?tab=overdue">View Overdue Books</Link>
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => setBannerDismissed(true)}
                  aria-label="Dismiss alert"
                >
                  <X className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        ) : null}

        {isLoading ? (
          <StatsSkeleton />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Books"
              value={summary?.total_books ?? 0}
              subText={`${summary?.total_copies ?? 0} total copies`}
              accent="blue"
              icon={<BookOpen className="size-8 opacity-60" aria-hidden />}
            />
            <StatCard
              label="Members"
              value={summary?.total_members ?? 0}
              accent="green"
              icon={<Users className="size-8 opacity-60" aria-hidden />}
            />
            <StatCard
              label="Active Loans"
              value={summary?.active_loans ?? 0}
              subText={`${summary?.loans_today ?? 0} borrowed today`}
              accent="orange"
              icon={
                <ArrowLeftRight className="size-8 opacity-60" aria-hidden />
              }
            />
            <StatCard
              label="Overdue"
              value={summary?.overdue_loans ?? 0}
              subText={`${summary?.returns_today ?? 0} returned today`}
              accent="red"
              pulse={overdueCount > 0}
              ringPulse={overdueCount > 0}
              icon={<AlertCircle className="size-8 opacity-60" aria-hidden />}
            />
          </div>
        )}

        <div>
          <h2 className="mb-4 text-lg font-semibold tracking-tight">
            Library Analytics
          </h2>
          <div className="grid gap-6 lg:grid-cols-5">
            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle>Lending Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyLendingChart />
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Books by Genre</CardTitle>
              </CardHeader>
              <CardContent>
                <GenrePieChart />
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Most Popular Books</CardTitle>
            </CardHeader>
            <CardContent>
              <TopBooksChart />
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Last 5 lending actions (borrowed or returned)
                </CardDescription>
              </div>
              <Button variant="link" className="h-auto p-0" asChild>
                <Link href="/lending">View All</Link>
              </Button>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <LoadingSkeleton rows={5} columns={5} />
              ) : data?.recentLoans.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No lending activity yet.
                </p>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Book</TableHead>
                        <TableHead>Member</TableHead>
                        <TableHead>Borrowed Date</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data?.recentLoans.map((loan) => (
                        <TableRow key={loan.id}>
                          <TableCell className="font-medium">
                            {loan.book_title}
                          </TableCell>
                          <TableCell>{loan.member_name}</TableCell>
                          <TableCell>{formatDate(loan.borrowed_at)}</TableCell>
                          <TableCell>{formatDate(loan.due_date)}</TableCell>
                          <TableCell>
                            {loan.returned_at ? (
                              <Badge
                                variant="secondary"
                                className="bg-slate-100 text-slate-700 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-200"
                              >
                                Returned
                              </Badge>
                            ) : (
                              <LoanStatusBadge status={getLoanStatus(loan)} />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <div className="mt-4 text-center">
                    <Button variant="link" className="h-auto p-0" asChild>
                      <Link href="/lending?tab=history">View Full History</Link>
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common library tasks</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => router.push("/books?action=add")}
              >
                <Plus className="size-4" aria-hidden />
                Add Book
              </Button>
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => router.push("/members?action=register")}
              >
                <UserPlus className="size-4" aria-hidden />
                Register Member
              </Button>
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => router.push("/lending?action=borrow")}
              >
                <ArrowLeftRight className="size-4" aria-hidden />
                Borrow Book
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
