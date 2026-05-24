"use client";

import {
  BrowserMultiFormatReader,
  type IScannerControls,
} from "@zxing/browser";
import { Check, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { normalizeISBNFromScan } from "@/lib/isbnUtils";
import { cn } from "@/lib/utils";

type ScannerStatus =
  | "initializing"
  | "scanning"
  | "detected"
  | "permission_denied"
  | "no_camera"
  | "error";

interface BarcodeScannerProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (result: string) => void;
  title?: string;
}

export function BarcodeScanner({
  isOpen,
  onClose,
  onScan,
  title = "Scan Barcode",
}: BarcodeScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const codeReaderRef = useRef<BrowserMultiFormatReader | null>(null);
  const scannerControlsRef = useRef<IScannerControls | null>(null);
  const hasDetectedRef = useRef(false);

  function stopVideoTracks() {
    const stream = videoRef.current?.srcObject;
    if (stream instanceof MediaStream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  const [status, setStatus] = useState<ScannerStatus>("initializing");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [manualISBN, setManualISBN] = useState("");
  const [showManualInput, setShowManualInput] = useState(false);

  const stopScanner = useCallback(() => {
    scannerControlsRef.current?.stop();
    scannerControlsRef.current = null;
    codeReaderRef.current = null;
    stopVideoTracks();
    hasDetectedRef.current = false;
  }, []);

  const handleClose = useCallback(() => {
    stopScanner();
    setManualISBN("");
    setShowManualInput(false);
    setStatus("initializing");
    setStatusMessage(null);
    onClose();
  }, [onClose, stopScanner]);

  const handleManualSubmit = useCallback(() => {
    const normalized = normalizeISBNFromScan(manualISBN);
    if (!normalized) {
      return;
    }
    stopScanner();
    onScan(normalized);
    handleClose();
  }, [manualISBN, onScan, stopScanner, handleClose]);

  useEffect(() => {
    if (!isOpen) {
      stopScanner();
      return;
    }

    hasDetectedRef.current = false;
    setStatus("initializing");
    setStatusMessage(null);
    setShowManualInput(false);
    setManualISBN("");

    let cancelled = false;

    async function startScanner() {
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;

      try {
        const devices = await BrowserMultiFormatReader.listVideoInputDevices();

        if (cancelled) {
          stopScanner();
          return;
        }

        if (devices.length === 0) {
          setStatus("no_camera");
          setShowManualInput(true);
          return;
        }

        const selectedDevice =
          devices.find((device) =>
            device.label.toLowerCase().includes("back"),
          ) ?? devices[0];

        if (!videoRef.current) {
          setStatus("error");
          setStatusMessage("Camera preview unavailable.");
          setShowManualInput(true);
          return;
        }

        setStatus("scanning");

        const controls = await codeReader.decodeFromVideoDevice(
          selectedDevice.deviceId,
          videoRef.current,
          (result, error) => {
            if (cancelled || hasDetectedRef.current) {
              return;
            }

            if (result) {
              hasDetectedRef.current = true;
              const text = normalizeISBNFromScan(result.getText());
              setStatus("detected");
              controls.stop();
              scannerControlsRef.current = null;
              stopVideoTracks();
              codeReaderRef.current = null;

              window.setTimeout(() => {
                onScan(text || result.getText());
              }, 400);
              return;
            }

            if (error && error.name !== "NotFoundException") {
              console.debug("Scan decode:", error);
            }
          },
        );

        if (!cancelled) {
          scannerControlsRef.current = controls;
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        const err = error as Error;
        if (err.name === "NotAllowedError") {
          setStatus("permission_denied");
          setStatusMessage(
            "Camera access denied. Please allow camera access in your browser settings and try again.",
          );
          setShowManualInput(true);
          return;
        }

        if (
          err.name === "NotFoundError" ||
          err.message?.toLowerCase().includes("no camera")
        ) {
          setStatus("no_camera");
          setShowManualInput(true);
          return;
        }

        setStatus("error");
        setStatusMessage(
          err.message || "Unable to start the camera. Try manual entry.",
        );
        setShowManualInput(true);
      }
    }

    void startScanner();

    return () => {
      cancelled = true;
      stopScanner();
    };
  }, [isOpen, onScan, stopScanner]);

  function renderStatusText() {
    if (status === "detected") {
      return (
        <p className="flex items-center justify-center gap-2 text-sm font-medium text-emerald-600">
          <Check className="size-4" aria-hidden />
          Detected!
        </p>
      );
    }

    if (status === "scanning" || status === "initializing") {
      return (
        <p className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Scanning…
        </p>
      );
    }

    if (statusMessage) {
      return <p className="text-center text-sm text-destructive">{statusMessage}</p>;
    }

    if (status === "no_camera") {
      return (
        <p className="text-center text-sm text-muted-foreground">
          No camera found on this device
        </p>
      );
    }

    return null;
  }

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          handleClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div className="relative overflow-hidden rounded-lg bg-black">
            <video
              ref={videoRef}
              className={cn(
                "aspect-[4/3] w-full object-cover",
                (status === "no_camera" ||
                  status === "permission_denied") &&
                  "hidden",
              )}
              muted
              playsInline
            />

            {status !== "no_camera" && status !== "permission_denied" ? (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/40">
                <div className="relative flex flex-col items-center">
                  <div
                    className={cn(
                      "h-32 w-56 rounded-md border-2 border-emerald-400 shadow-[0_0_12px_rgba(74,222,128,0.5)]",
                      status === "scanning" && "animate-pulse",
                    )}
                  />
                  <p className="mt-3 max-w-[240px] text-center text-xs text-white/90">
                    Point camera at barcode or QR code
                  </p>
                </div>
              </div>
            ) : null}
          </div>

          {renderStatusText()}

          {showManualInput ? (
            <div className="space-y-2 rounded-lg border bg-muted/30 p-3">
              <Label htmlFor="manual-isbn">Or enter ISBN manually:</Label>
              <div className="flex gap-2">
                <Input
                  id="manual-isbn"
                  value={manualISBN}
                  onChange={(event) => setManualISBN(event.target.value)}
                  placeholder="13-digit ISBN"
                  inputMode="numeric"
                />
                <Button
                  type="button"
                  onClick={handleManualSubmit}
                  disabled={!manualISBN.trim()}
                >
                  Use This ISBN
                </Button>
              </div>
            </div>
          ) : null}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
