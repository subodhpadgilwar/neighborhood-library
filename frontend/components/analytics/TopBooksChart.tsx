"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Skeleton } from "@/components/ui/skeleton";
import { analyticsService } from "@/services";
import type { TopBookStats } from "@/types";

function truncateTitle(title: string, maxLength = 20): string {
  if (title.length <= maxLength) {
    return title;
  }
  return `${title.slice(0, maxLength - 3)}...`;
}

type ChartRow = TopBookStats & { displayTitle: string };

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ChartRow }[];
}) {
  if (!active || !payload?.[0]) {
    return null;
  }
  const book = payload[0].payload;
  return (
    <div className="max-w-xs rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      <p className="font-medium">
        {book.title} by {book.author}
      </p>
      <p className="text-muted-foreground">
        Genre: {book.genre || "Uncategorized"}
      </p>
      <p className="text-muted-foreground">
        Shelf: {book.shelf_location || "Not specified"}
      </p>
      <p>Total Borrows: {book.total_borrows}</p>
      <p>Currently Out: {book.current_borrows}</p>
      <p>Utilization: {book.utilization_rate.toFixed(1)}%</p>
    </div>
  );
}

export function TopBooksChart() {
  const [data, setData] = useState<TopBookStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await analyticsService.getTopBooks(5);
        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          const apiError = err as { message?: string };
          setError(
            typeof apiError?.message === "string"
              ? apiError.message
              : "Failed to load top books.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const chartData = useMemo<ChartRow[]>(
    () =>
      data.map((book) => ({
        ...book,
        displayTitle: truncateTitle(book.title),
      })),
    [data],
  );

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  if (data.length === 0) {
    return (
      <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
        No borrowing data yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-muted-foreground">
        Top {data.length} Most Borrowed Books
      </p>
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} horizontal={false} />
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="displayTitle"
              width={150}
              tick={{ fontSize: 11 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="total_borrows"
              fill="#6366f1"
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
