"use client";

import { useCallback, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { cn } from "@/lib/utils";
import { analyticsService } from "@/services";
import type { MonthlyLendingStats } from "@/types";

const MONTH_OPTIONS = [3, 6, 12, 24] as const;

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      <p className="mb-1 font-medium">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
}

export function MonthlyLendingChart() {
  const [months, setMonths] = useState<number>(6);
  const [data, setData] = useState<MonthlyLendingStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (selectedMonths: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyticsService.getMonthlyLending(selectedMonths);
      setData(result);
    } catch (err) {
      const apiError = err as { message?: string };
      setError(
        typeof apiError?.message === "string"
          ? apiError.message
          : "Failed to load lending trends.",
      );
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useDeferredEffect(() => {
    void loadData(months);
  }, [months, loadData]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {MONTH_OPTIONS.map((option) => (
          <Button
            key={option}
            type="button"
            size="sm"
            variant={months === option ? "default" : "outline"}
            className={cn("min-w-12 tabular-nums")}
            onClick={() => setMonths(option)}
          >
            {option}M
          </Button>
        ))}
      </div>

      {isLoading ? (
        <Skeleton className="h-[300px] w-full" />
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
          No lending data yet
        </div>
      ) : (
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={data}
              margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="top" />
              <Bar
                dataKey="total_loans"
                name="Total Loans"
                fill="#6366f1"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="returned_loans"
                name="Returned"
                fill="#10b981"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="overdue_loans"
                name="Overdue"
                fill="#ef4444"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
