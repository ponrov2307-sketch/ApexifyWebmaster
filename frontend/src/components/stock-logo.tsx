"use client";

import { useState } from "react";
import { logoUrl } from "@/lib/dashboard-helpers";

interface Props {
  ticker: string;
  size?: number;
  className?: string;
}

const COLORS = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"];

function Fallback({ ticker, size, className }: Props) {
  const idx = (ticker.charCodeAt(0) + (ticker.charCodeAt(1) || 0)) % COLORS.length;
  const color = COLORS[idx];
  return (
    <div
      className={`flex items-center justify-center rounded-full shrink-0 ${className || ""}`}
      style={{
        width: size,
        height: size,
        background: `linear-gradient(135deg, ${color}33, ${color}11)`,
        border: `1.5px solid ${color}55`,
      }}
    >
      <span style={{ fontSize: (size || 32) * 0.35, color, fontWeight: 800, letterSpacing: 1 }}>
        {ticker.replace(".BK", "").slice(0, 2)}
      </span>
    </div>
  );
}

export default function StockLogo({ ticker, size = 32, className = "" }: Props) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return <Fallback ticker={ticker} size={size} className={className} />;
  }

  return (
    <div className={`relative shrink-0 ${className}`} style={{ width: size, height: size }}>
      {/* Fallback behind the image — shows instantly while image loads */}
      <div className="absolute inset-0">
        <Fallback ticker={ticker} size={size} />
      </div>
      <img
        src={logoUrl(ticker)}
        alt={ticker}
        className="rounded-full relative z-10"
        style={{ width: size, height: size, objectFit: "cover" }}
        loading="lazy"
        onError={() => setFailed(true)}
        onLoad={(e) => {
          // If image loaded but is too small (fallback SVG from our API), keep it
          const img = e.currentTarget;
          if (img.naturalWidth < 10) setFailed(true);
        }}
      />
    </div>
  );
}
