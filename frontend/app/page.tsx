"use client";

import {
  differenceInCalendarDays,
  format,
  parseISO,
  startOfDay,
} from "date-fns";
import {
  AlertTriangle,
  BookOpen,
  Plus,
  UserPlus,
  ArrowLeftRight,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppLayout } from "@/components/layout/AppLayout";
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
import { cn } from "@/lib/utils";
import {
  bookService,
  lendingService,
  memberService,
} from "@/services";
import type { Lending } from "@/types";

type LoanStatus = "overdue" | "due-soon" | "active";

interface DashboardData {
  booksCount: number;
  membersCount: number;
  activeLoansCount: number;
  overdueCount: number;
  recentLoans: Lending[];
}

function getLoanStatus(lending: Lending): LoanStatus {
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

function formatDate(iso: string): string {
  return format(parseISO(iso), "MMM d, yyyy");
}

function LoanStatusBadge({ status }: { status: LoanStatus }) {
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

interface StatCardProps {
  label: string;
  value: number | string;
  accent: "blue" | "green" | "orange" | "red";
  pulse?: boolean;
  badge?: number;
}

const accentStyles = {
  blue: "border-l-blue-500 bg-blue-50/60 dark:bg-blue-950/30",
  green: "border-l-emerald-500 bg-emerald-50/60 dark:bg-emerald-950/30",
  orange: "border-l-orange-500 bg-orange-50/60 dark:bg-orange-950/30",
  red: "border-l-red-500 bg-red-50/60 dark:bg-red-950/30",
} as const;

function StatCard({ label, value, accent, pulse, badge }: StatCardProps) {
  return (
    <Card
      className={cn(
        "border-l-4 py-4 shadow-none",
        accentStyles[accent],
        pulse && "animate-pulse",
      )}
    >
      <CardContent className="flex items-start justify-between px-4 py-0">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-3xl font-semibold tracking-tight">{value}</p>
        </div>
        {badge !== undefined && badge > 0 ? (
          <Badge variant="destructive" className="tabular-nums">
            {badge}
          </Badge>
        ) : null}
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

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
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
        bookService.getAll(),
        memberService.getAll(),
        lendingService.getAllActive(),
        lendingService.getOverdue(),
      ]);

      if (cancelled) {
        return;
      }

      const labels = ["books", "members", "active loans", "overdue loans"];
      const errors: string[] = [];

      const books =
        results[0].status === "fulfilled" ? results[0].value : [];
      const members =
        results[1].status === "fulfilled" ? results[1].value : [];
      const activeLoans =
        results[2].status === "fulfilled" ? results[2].value : [];
      const overdueLoans =
        results[3].status === "fulfilled" ? results[3].value : [];

      results.forEach((result, index) => {
        if (result.status === "rejected") {
          errors.push(`Failed to load ${labels[index]}`);
        }
      });

      if (errors.length > 0) {
        setError(errors.join(". ") + ".");
      }

      const recentLoans = [...activeLoans]
        .sort(
          (a, b) =>
            parseISO(b.borrowed_at).getTime() - parseISO(a.borrowed_at).getTime(),
        )
        .slice(0, 5);

      setData({
        booksCount: books.length,
        membersCount: members.length,
        activeLoansCount: activeLoans.length,
        overdueCount: overdueLoans.length,
        recentLoans,
      });
      setIsLoading(false);
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  const overdueCount = data?.overdueCount ?? 0;
  const showBanner = !bannerDismissed && !isLoading && overdueCount > 0;

  const overdueMessage = `${overdueCount} book(s) are overdue and need attention`;

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6">
        {error ? (
          <div
            role="alert"
            className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {error} Some figures may be incomplete.
          </div>
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
              label="Total Books"
              value={data?.booksCount ?? 0}
              accent="blue"
            />
            <StatCard
              label="Total Members"
              value={data?.membersCount ?? 0}
              accent="green"
            />
            <StatCard
              label="Active Loans"
              value={data?.activeLoansCount ?? 0}
              accent="orange"
            />
            <StatCard
              label="Overdue Books"
              value={data?.overdueCount ?? 0}
              accent="red"
              pulse={overdueCount > 0}
              badge={overdueCount > 0 ? overdueCount : undefined}
            />
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Last 5 active loans</CardDescription>
              </div>
              <Button variant="link" className="h-auto p-0" asChild>
                <Link href="/lending">View All</Link>
              </Button>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <TableSkeleton />
              ) : data?.recentLoans.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No active loans yet.
                </p>
              ) : (
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
                          <LoanStatusBadge status={getLoanStatus(loan)} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
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
