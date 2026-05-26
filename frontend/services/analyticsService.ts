import { api } from "@/lib/api";
import { apiPaths } from "@/lib/apiPaths";
import type {
  GenreStats,
  MonthlyLendingStats,
  SummaryStats,
  TopBookStats,
} from "@/types";

export async function getSummary(): Promise<SummaryStats> {
  const { data } = await api.get<SummaryStats>(apiPaths.analytics.summary);
  return data;
}

export async function getGenreDistribution(): Promise<GenreStats[]> {
  const { data } = await api.get<GenreStats[]>(
    apiPaths.analytics.genreDistribution,
  );
  return data;
}

export async function getMonthlyLending(
  months = 6,
): Promise<MonthlyLendingStats[]> {
  const { data } = await api.get<MonthlyLendingStats[]>(
    apiPaths.analytics.monthlyLending,
    { params: { months } },
  );
  return data;
}

export async function getTopBooks(limit = 5): Promise<TopBookStats[]> {
  const { data } = await api.get<TopBookStats[]>(apiPaths.analytics.topBooks, {
    params: { limit },
  });
  return data;
}
