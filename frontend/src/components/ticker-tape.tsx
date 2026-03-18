"use client";

import { useEffect, useState } from "react";
import { useLang, tr } from "@/lib/i18n";
import api from "@/lib/api";

interface TickerItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
}

const DISPLAY_NAMES: Record<string, string> = {
  "^GSPC": "S&P 500",
  "^DJI": "DOW",
  "^IXIC": "NASDAQ",
  "^SET.BK": "SET",
  "BTC-USD": "BITCOIN",
  "GC=F": "GOLD",
};

export default function TickerTape() {
  const [items, setItems] = useState<TickerItem[]>([]);
  const { lang } = useLang();

  useEffect(() => {
    let cancelled = false;

    const fetchPrices = async () => {
      try {
        // Use /api/market/macro — returns indices as a proper dict keyed by symbol
        const { data } = await api.get("/api/market/macro");
        const indices: Record<string, { name: string; price: number }> =
          data.indices || {};

        if (cancelled) return;

        const tickers: TickerItem[] = [];

        // Build ticker items from the macro indices dict
        for (const [sym, info] of Object.entries(indices)) {
          const displayName = DISPLAY_NAMES[sym] || info.name || sym;
          const price = typeof info.price === "number" ? info.price : parseFloat(String(info.price)) || 0;
          tickers.push({
            symbol: sym,
            name: displayName,
            price,
            change: 0, // macro endpoint doesn't provide change %, will show price only
          });
        }

        // Also fetch THB=X separately (not in macro)
        try {
          const { data: thbData } = await api.get("/api/market/price/THB=X");
          if (!cancelled && thbData.price) {
            tickers.push({
              symbol: "THB=X",
              name: "USD/THB",
              price: thbData.price,
              change: 0,
            });
          }
        } catch {
          /* ignore */
        }

        if (!cancelled && tickers.length > 0) {
          setItems(tickers);
        }
      } catch {
        /* ignore */
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 20000); // refresh every 20s for real-time feel
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (items.length === 0) return null;

  // Duplicate items 3x for seamless infinite scroll
  const allItems = [...items, ...items, ...items];

  return (
    <div
      className="fixed top-[52px] left-0 right-0 z-40 h-[44px] overflow-hidden"
      style={{
        background:
          "linear-gradient(90deg, rgba(6,16,24,0.92), rgba(10,25,34,0.92), rgba(6,16,24,0.92))",
        backdropFilter: "blur(16px)",
        borderTop: "1px solid rgba(86, 211, 255, 0.16)",
        borderBottom: "1px solid rgba(126, 247, 207, 0.1)",
      }}
    >
      {/* Live pill */}
      <div className="absolute left-3 top-1/2 -translate-y-1/2 z-10 flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[#56D3FF]/30 bg-[#56D3FF]/10">
        <span className="w-1.5 h-1.5 rounded-full bg-[#32D74B] animate-pulse" />
        <span className="text-[10px] font-black text-[#56D3FF] tracking-wider">
          {tr("common.live_feed", lang)}
        </span>
      </div>

      {/* Scrolling content */}
      <div className="flex items-center h-full ml-24">
        <div className="flex items-center gap-0 animate-ticker whitespace-nowrap">
          {allItems.map((item, i) => {
            const isTHB = item.symbol === "THB=X";
            const prefix = isTHB ? "฿" : "$";

            return (
              <div
                key={`${item.symbol}-${i}`}
                className="flex items-center px-5 gap-2"
              >
                <span className="text-[11px] font-black text-[#8B949E] tracking-wider">
                  {item.name}
                </span>
                <span className="text-[12px] font-bold text-white tabular-nums">
                  {prefix}
                  {item.price > 1000
                    ? item.price.toLocaleString("en-US", {
                        maximumFractionDigits: 0,
                      })
                    : item.price.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                </span>
                {/* Dot separator */}
                <span className="w-1 h-1 rounded-full bg-white/20" />
              </div>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        @keyframes ticker-scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-33.333%);
          }
        }
        .animate-ticker {
          animation: ticker-scroll 40s linear infinite;
        }
        .animate-ticker:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
