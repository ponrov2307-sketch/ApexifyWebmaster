"use client";

import { useNews } from "@/lib/hooks";
import {
  Newspaper,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
} from "lucide-react";
import ProGate from "@/components/pro-gate";

function parseSentiment(summary: string): "positive" | "negative" | "neutral" {
  const lower = summary.toLowerCase();
  const pos = ["bullish", "surge", "gain", "rise", "up", "growth", "beat", "strong", "high", "rally"];
  const neg = ["bearish", "drop", "fall", "decline", "down", "loss", "miss", "weak", "low", "crash"];
  let score = 0;
  for (const w of pos) if (lower.includes(w)) score++;
  for (const w of neg) if (lower.includes(w)) score--;
  if (score > 0) return "positive";
  if (score < 0) return "negative";
  return "neutral";
}

const sentimentConfig = {
  positive: { icon: TrendingUp, color: "#32D74B", bg: "rgba(50,215,75,0.1)", label: "Bullish" },
  negative: { icon: TrendingDown, color: "#FF453A", bg: "rgba(255,69,58,0.1)", label: "Bearish" },
  neutral: { icon: Minus, color: "#8B949E", bg: "rgba(139,148,158,0.1)", label: "Neutral" },
};

export default function NewsPage() {
  const { news, loading } = useNews();

  return (
    <ProGate>
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
          <Newspaper className="text-[#39C8FF]" size={24} />
          AI News Feed
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          AI-powered news summaries for your portfolio stocks
        </p>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
          <p className="text-gray-500 text-sm">Fetching news from AI...</p>
        </div>
      ) : news.length === 0 ? (
        <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center">
          <Newspaper className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-bold text-white mb-2">No news available</h2>
          <p className="text-gray-500 text-sm">
            Add stocks to your portfolio to see AI-summarized news
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {news.map((item) => {
            const sentiment = parseSentiment(item.summary);
            const config = sentimentConfig[sentiment];
            const SentimentIcon = config.icon;

            return (
              <div
                key={item.ticker}
                className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden hover:border-white/15 transition-colors"
              >
                {/* Card header */}
                <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-sm font-black text-white">
                      {item.ticker.slice(0, 2)}
                    </div>
                    <div>
                      <span className="font-black text-white text-lg tracking-wide">
                        {item.ticker}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <Sparkles size={10} className="text-[#39C8FF]" />
                        <span className="text-[10px] text-[#39C8FF] font-bold">
                          AI Summary
                        </span>
                      </div>
                    </div>
                  </div>
                  <div
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold"
                    style={{ background: config.bg, color: config.color }}
                  >
                    <SentimentIcon size={14} />
                    {config.label}
                  </div>
                </div>

                {/* Summary content */}
                <div className="px-5 py-4">
                  <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {item.summary || "No news summary available at this time."}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
    </ProGate>
  );
}
