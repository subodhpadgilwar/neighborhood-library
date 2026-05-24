import { api } from "@/lib/api";
import type {
  GenreStats,
  MonthlyLendingStats,
  SummaryStats,
  TopBookStats,
} from "@/types";

export async function getSummary(): Promise<SummaryStats> {
  const { data } = await api.get<SummaryStats>("/analytics/summary");
  return data;
}

export async function getGenreDistribution(): Promise<GenreStats[]> {
  const { data } = await api.get<GenreStats[]>("/analytics/genre-distribution");
  return data;
}

export async function getMonthlyLending(
  months = 6,
): Promise<MonthlyLendingStats[]> {
  const { data } = await api.get<MonthlyLendingStats[]>(
    "/analytics/monthly-lending",
    { params: { months } },
  );
  return data;
}

export async function getTopBooks(limit = 5): Promise<TopBookStats[]> {
  const { data } = await api.get<TopBookStats[]>("/analytics/top-books", {
    params: { limit },
  });
  return data;
}
