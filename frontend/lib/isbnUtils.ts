/** Extract a 13-digit ISBN from raw barcode or QR text. */
export function normalizeISBNFromScan(raw: string): string {
  const trimmed = raw.trim();
  const isbnMatch = trimmed.match(/(?:isbn[:\s-]*)?(\d{10,13})/i);
  const digits = (isbnMatch?.[1] ?? trimmed).replace(/\D/g, "");

  if (digits.length >= 13) {
    return digits.slice(-13);
  }

  return digits;
}
