"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { Skeleton } from "@/components/ui/skeleton";
import { analyticsService } from "@/services";
import type { GenreStats } from "@/types";

const CHART_COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
  "#f97316",
  "#14b8a6",
  "#84cc16",
  "#06b6d4",
];

function ChartSkeleton() {
  return (
    <div className="flex flex-col items-center gap-4 py-4">
      <Skeleton className="size-48 rounded-full" />
      <div className="flex flex-wrap justify-center gap-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-24" />
        ))}
      </div>
    </div>
  );
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: GenreStats }[];
}) {
  if (!active || !payload?.[0]) {
    return null;
  }
  const item = payload[0].payload;
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-sm shadow-md">
      {item.genre}: {item.total_books} books ({item.percentage.toFixed(1)}%)
    </div>
  );
}

export function GenrePieChart() {
  const [data, setData] = useState<GenreStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await analyticsService.getGenreDistribution();
        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          const apiError = err as { message?: string };
          setError(
            typeof apiError?.message === "string"
              ? apiError.message
              : "Failed to load genre distribution.",
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

  const totalBooks = useMemo(
    () => data.reduce((sum, item) => sum + item.total_books, 0),
    [data],
  );

  if (isLoading) {
    return <ChartSkeleton />;
  }

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] flex-col items-center justify-center text-center text-sm text-muted-foreground">
        <p className="font-medium">No genre data available</p>
        <p className="mt-1">Add genres to your books to see distribution</p>
      </div>
    );
  }

  return (
    <div className="relative h-[300px] w-full">
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="total_books"
            nameKey="genre"
            cx="50%"
            cy="45%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell
                key={entry.genre}
                fill={CHART_COLORS[index % CHART_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            formatter={(value, entry) => {
              const item = entry.payload as GenreStats | undefined;
              const color =
                CHART_COLORS[
                  data.findIndex((row) => row.genre === value) %
                    CHART_COLORS.length
                ];
              return (
                <span className="inline-flex items-center gap-1.5 text-xs text-foreground">
                  <span
                    className="inline-block size-2.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  {value} ({item?.total_books ?? 0})
                </span>
              );
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
        <p className="text-2xl font-semibold tabular-nums">{totalBooks}</p>
        <p className="text-xs text-muted-foreground">Total Books</p>
      </div>
    </div>
  );
}
