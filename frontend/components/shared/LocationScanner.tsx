"use client";

import { Camera, Check } from "lucide-react";
import { useEffect, useState } from "react";

import { BarcodeScanner } from "@/components/shared/BarcodeScanner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface LocationScannerProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function LocationScanner({
  value,
  onChange,
  placeholder = "e.g. Section A - Shelf 3",
  disabled = false,
}: LocationScannerProps) {
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [scannedFlash, setScannedFlash] = useState<string | null>(null);

  useEffect(() => {
    if (!scannedFlash) {
      return;
    }
    const timer = window.setTimeout(() => setScannedFlash(null), 2000);
    return () => window.clearTimeout(timer);
  }, [scannedFlash]);

  function handleScan(result: string) {
    const trimmed = result.trim();
    onChange(trimmed);
    setScannedFlash(trimmed);
    setIsScannerOpen(false);
  }

  return (
    <div className="space-y-1">
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            scannedFlash &&
              "border-emerald-400 ring-1 ring-emerald-400/50 dark:border-emerald-600",
          )}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="shrink-0 gap-1.5"
          onClick={() => setIsScannerOpen(true)}
          disabled={disabled}
          title="Scan location barcode or QR"
        >
          <Camera className="size-4" aria-hidden />
          Scan
        </Button>
      </div>
      {scannedFlash ? (
        <p className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
          <Check className="size-3.5" aria-hidden />
          Scanned: {scannedFlash}
        </p>
      ) : null}

      <BarcodeScanner
        isOpen={isScannerOpen}
        onClose={() => setIsScannerOpen(false)}
        onScan={handleScan}
        title="Scan Shelf Location"
        transformScan={(raw) => raw.trim()}
        manualInputLabel="Or enter location manually:"
        manualInputPlaceholder="Shelf location"
      />
    </div>
  );
}
