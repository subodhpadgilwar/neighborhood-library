/** Converts UI page/limit to API skip offset. */
export function pageLimitToSkip(page: number, limit: number): number {
  return Math.max(0, (page - 1) * limit);
}
