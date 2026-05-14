"use client";

// RecoBboxCrop — canvas drawing of the audit screenshot with a red rectangle
// overlay at the reco's `bbox` coordinates (Sprint 5 / Task 006).
//
// Source pattern : V26 HTML L2475-2510 (renderRecoCard bbox snippet).
//
// Bbox coordinate convention :
// - 4-tuple `[x1, y1, x2, y2]` (top-left + bottom-right)
// - Values in [0, 1] are treated as normalized (% of source dimensions)
// - Values > 1 are treated as absolute pixels
// - Out-of-bounds is clamped to image dimensions
//
// Renders nothing when bbox is absent or invalid — the parent (RichRecoCard)
// already gates this with a `bbox != null` check before mounting.
//
// Lazy by design : the canvas only mounts when the parent reco card is
// expanded ; nothing is decoded until the component appears.

import { useEffect, useRef, useState } from "react";

export type Bbox = [number, number, number, number];

type Props = {
  screenshotUrl: string;
  bbox: Bbox;
  alt: string;
  maxWidth?: number;
};

const RED = "#e87555";

function clamp(v: number, min: number, max: number): number {
  if (Number.isNaN(v)) return min;
  return Math.min(max, Math.max(min, v));
}

export function RecoBboxCrop({ screenshotUrl, bbox, alt, maxWidth = 480 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let cancelled = false;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      if (cancelled) return;
      const targetW = Math.min(maxWidth, img.naturalWidth || maxWidth);
      const scale = targetW / Math.max(1, img.naturalWidth);
      const targetH = (img.naturalHeight || maxWidth) * scale;
      canvas.width = targetW;
      canvas.height = targetH;
      ctx.drawImage(img, 0, 0, targetW, targetH);

      // Normalize bbox coordinates.
      const [x1, y1, x2, y2] = bbox;
      const isNormalized =
        x1 >= 0 && x1 <= 1 && x2 >= 0 && x2 <= 1 && y1 >= 0 && y1 <= 1 && y2 >= 0 && y2 <= 1;
      const sx1 = isNormalized ? x1 * img.naturalWidth : x1;
      const sy1 = isNormalized ? y1 * img.naturalHeight : y1;
      const sx2 = isNormalized ? x2 * img.naturalWidth : x2;
      const sy2 = isNormalized ? y2 * img.naturalHeight : y2;

      const rx = clamp(sx1 * scale, 0, targetW);
      const ry = clamp(sy1 * scale, 0, targetH);
      const rw = clamp((sx2 - sx1) * scale, 0, targetW - rx);
      const rh = clamp((sy2 - sy1) * scale, 0, targetH - ry);

      ctx.strokeStyle = RED;
      ctx.lineWidth = 3;
      ctx.strokeRect(rx, ry, rw, rh);

      // Subtle red glow / fill to draw the eye to the box without obscuring.
      ctx.fillStyle = "rgba(232, 117, 85, 0.12)";
      ctx.fillRect(rx, ry, rw, rh);
    };
    img.onerror = () => {
      if (!cancelled) setError("screenshot_load_failed");
    };
    img.src = screenshotUrl;

    return () => {
      cancelled = true;
    };
  }, [screenshotUrl, bbox, maxWidth]);

  if (error) {
    return (
      <p
        style={{
          fontSize: 11,
          color: "var(--gc-muted)",
          fontStyle: "italic",
          margin: "8px 0",
        }}
      >
        Capture indisponible.
      </p>
    );
  }

  return (
    <a
      href={screenshotUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Ouvrir la capture complète : ${alt}`}
      data-testid="reco-bbox-crop"
      style={{
        display: "block",
        borderRadius: 8,
        overflow: "hidden",
        border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
        background: "var(--gc-panel-2, rgba(255,255,255,0.02))",
        maxWidth,
        width: "100%",
      }}
    >
      <canvas ref={canvasRef} style={{ display: "block", width: "100%", height: "auto" }} />
    </a>
  );
}
