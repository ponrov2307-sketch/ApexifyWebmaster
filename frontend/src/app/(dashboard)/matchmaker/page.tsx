"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { usePortfolio } from "@/lib/hooks";
import api from "@/lib/api";
import Sparkline from "@/components/sparkline";
import StockLogo from "@/components/stock-logo";
import {
  Heart,
  Loader2,
  Sparkles,
  RotateCcw,
  TrendingUp,
  DollarSign,
  Target,
  Activity,
  BarChart3,
  Shield,
  X,
  Check,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import ProGate from "@/components/pro-gate";

interface Recommendation {
  ticker: string;
  name: string;
  reason: string;
  sector: string;
  match_score: number;
  price?: number;
  market_cap?: number;
  pe_ratio?: number;
  div_yield?: number;
  "52w_high"?: number;
  "52w_low"?: number;
  beta?: number;
  target_price?: number;
  recommendation?: string;
  sparkline?: number[];
}

function fmtMcap(n: number): string {
  if (!n) return "—";
  if (n >= 1e12) return "$" + (n / 1e12).toFixed(2) + "T";
  if (n >= 1e9) return "$" + (n / 1e9).toFixed(1) + "B";
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(0) + "M";
  return "$" + n.toLocaleString();
}

function recColor(rec: string): string {
  if (rec === "buy" || rec === "strong_buy") return "#32D74B";
  if (rec === "sell" || rec === "strong_sell") return "#FF453A";
  return "#FCD535";
}

function recLabel(rec: string): string {
  const map: Record<string, string> = {
    strong_buy: "STRONG BUY",
    buy: "BUY",
    hold: "HOLD",
    sell: "SELL",
    strong_sell: "STRONG SELL",
  };
  return map[rec] || rec.toUpperCase() || "—";
}

/* ── Swipeable Card Component ── */
function SwipeCard({
  rec,
  onSwipeRight,
  onSwipeLeft,
  isTop,
}: {
  rec: Recommendation;
  onSwipeRight: () => void;
  onSwipeLeft: () => void;
  isTop: boolean;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const startX = useRef(0);
  const currentX = useRef(0);
  const isDragging = useRef(false);
  const [offset, setOffset] = useState(0);
  const [opacity, setOpacity] = useState(1);
  const [exitDir, setExitDir] = useState<"left" | "right" | null>(null);

  const SWIPE_THRESHOLD = 100;

  const handleStart = useCallback((clientX: number) => {
    if (!isTop) return;
    isDragging.current = true;
    startX.current = clientX;
    currentX.current = clientX;
  }, [isTop]);

  const handleMove = useCallback((clientX: number) => {
    if (!isDragging.current) return;
    currentX.current = clientX;
    const diff = clientX - startX.current;
    setOffset(diff);
    setOpacity(Math.max(0.5, 1 - Math.abs(diff) / 400));
  }, []);

  const handleEnd = useCallback(() => {
    if (!isDragging.current) return;
    isDragging.current = false;
    const diff = currentX.current - startX.current;

    if (diff > SWIPE_THRESHOLD) {
      setExitDir("right");
      setOffset(500);
      setOpacity(0);
      setTimeout(onSwipeRight, 250);
    } else if (diff < -SWIPE_THRESHOLD) {
      setExitDir("left");
      setOffset(-500);
      setOpacity(0);
      setTimeout(onSwipeLeft, 250);
    } else {
      setOffset(0);
      setOpacity(1);
    }
  }, [onSwipeRight, onSwipeLeft]);

  // Mouse events
  const onMouseDown = (e: React.MouseEvent) => handleStart(e.clientX);
  const onMouseMove = (e: React.MouseEvent) => handleMove(e.clientX);
  const onMouseUp = () => handleEnd();
  const onMouseLeave = () => { if (isDragging.current) handleEnd(); };

  // Touch events
  const onTouchStart = (e: React.TouchEvent) => handleStart(e.touches[0].clientX);
  const onTouchMove = (e: React.TouchEvent) => handleMove(e.touches[0].clientX);
  const onTouchEnd = () => handleEnd();

  const rotation = offset * 0.05;
  const showLike = offset > 40;
  const showNope = offset < -40;
  const sparkUp = rec.sparkline && rec.sparkline.length > 1 ? rec.sparkline[rec.sparkline.length - 1] >= rec.sparkline[0] : true;

  return (
    <div
      ref={cardRef}
      className={`absolute inset-0 rounded-3xl border overflow-hidden select-none ${isTop ? "cursor-grab active:cursor-grabbing z-10" : "z-0"}`}
      style={{
        background: "var(--bg-card)",
        borderColor: showLike ? "#32D74B" : showNope ? "#FF453A" : "var(--border-default)",
        transform: `translateX(${offset}px) rotate(${rotation}deg)`,
        opacity,
        transition: exitDir || !isDragging.current ? "all 0.3s ease-out" : "none",
        boxShadow: isTop ? "0 10px 40px rgba(0,0,0,0.3)" : "0 5px 20px rgba(0,0,0,0.15)",
      }}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseLeave}
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      {/* LIKE / NOPE stamp */}
      {showLike && (
        <div className="absolute top-8 left-8 z-20 border-4 border-[#32D74B] rounded-xl px-4 py-2 -rotate-12">
          <span className="text-3xl font-black text-[#32D74B] tracking-wider">LIKE</span>
        </div>
      )}
      {showNope && (
        <div className="absolute top-8 right-8 z-20 border-4 border-[#FF453A] rounded-xl px-4 py-2 rotate-12">
          <span className="text-3xl font-black text-[#FF453A] tracking-wider">NOPE</span>
        </div>
      )}

      {/* Card content */}
      <div className="h-full flex flex-col p-5 overflow-y-auto">
        {/* Tags row */}
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#D0FD3E]/10 text-[#D0FD3E]">
            <TrendingUp size={12} />
            <span className="text-xs font-black">{rec.match_score}% Match</span>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-[#39C8FF]/10 text-[#39C8FF]">
            {rec.sector}
          </span>
          {rec.recommendation && (
            <span
              className="text-xs font-black px-2.5 py-1 rounded-lg"
              style={{ color: recColor(rec.recommendation), background: `${recColor(rec.recommendation)}15` }}
            >
              {recLabel(rec.recommendation)}
            </span>
          )}
        </div>

        {/* Logo + Name + Price */}
        <div className="flex items-center gap-4 mb-4">
          <StockLogo ticker={rec.ticker} size={64} className="border-2 rounded-2xl" />
          <div className="flex-1 min-w-0">
            <h2 className="text-3xl font-black leading-none" style={{ color: "var(--text-primary)" }}>{rec.ticker}</h2>
            <p className="text-sm truncate mt-1" style={{ color: "var(--text-muted)" }}>{rec.name}</p>
          </div>
          {rec.price && rec.price > 0 && (
            <p className="text-2xl font-black tabular-nums" style={{ color: "var(--text-primary)" }}>
              ${rec.price.toFixed(2)}
            </p>
          )}
        </div>

        {/* Sparkline */}
        {rec.sparkline && rec.sparkline.length > 1 && (
          <div className="h-24 w-full rounded-xl overflow-hidden mb-4" style={{ background: "var(--input-bg)" }}>
            <Sparkline data={rec.sparkline} width={500} height={96} positive={sparkUp} />
          </div>
        )}

        {/* AI Reason */}
        <p className="text-sm leading-relaxed mb-4" style={{ color: "var(--text-secondary)" }}>
          {rec.reason}
        </p>

        {/* Financial grid */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          {[
            { icon: BarChart3, label: "MCap", value: fmtMcap(rec.market_cap || 0), color: "#39C8FF" },
            { icon: Activity, label: "P/E", value: rec.pe_ratio ? rec.pe_ratio.toFixed(1) : "—", color: "#FCD535" },
            { icon: DollarSign, label: "Div%", value: rec.div_yield ? `${rec.div_yield.toFixed(2)}%` : "—", color: "#32D74B" },
            { icon: Shield, label: "Beta", value: rec.beta ? rec.beta.toFixed(2) : "—", color: "#AF52DE" },
          ].map((stat) => (
            <div key={stat.label} className="text-center p-2 rounded-xl" style={{ background: "var(--bg-surface)" }}>
              <div className="flex items-center justify-center gap-1 mb-1">
                <stat.icon size={10} style={{ color: stat.color }} />
                <span className="text-[9px] font-bold uppercase" style={{ color: "var(--text-dim)" }}>{stat.label}</span>
              </div>
              <p className="text-sm font-black tabular-nums" style={{ color: "var(--text-primary)" }}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* 52w range */}
        {rec["52w_low"] && rec["52w_high"] && rec.price ? (
          <div className="px-1 mb-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] tabular-nums" style={{ color: "var(--text-dim)" }}>${rec["52w_low"].toFixed(0)}</span>
              <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
                <div
                  className="h-full rounded-full bg-[#39C8FF]"
                  style={{ width: `${Math.min(100, Math.max(2, ((rec.price - rec["52w_low"]) / (rec["52w_high"] - rec["52w_low"])) * 100))}%` }}
                />
              </div>
              <span className="text-[10px] tabular-nums" style={{ color: "var(--text-dim)" }}>${rec["52w_high"].toFixed(0)}</span>
            </div>
          </div>
        ) : null}

        {/* Analyst target */}
        {rec.target_price && rec.target_price > 0 && rec.price ? (
          <div className="flex items-center gap-2 px-1">
            <Target size={12} className="text-[#FCD535]" />
            <span className="text-[10px] font-bold" style={{ color: "var(--text-dim)" }}>Target</span>
            <span className="text-sm font-black tabular-nums" style={{ color: "var(--text-primary)" }}>
              ${rec.target_price.toFixed(2)}
            </span>
            <span
              className="text-xs font-bold px-2 py-0.5 rounded tabular-nums"
              style={{
                color: rec.target_price >= rec.price ? "#32D74B" : "#FF453A",
                background: rec.target_price >= rec.price ? "rgba(50,215,75,0.1)" : "rgba(255,69,58,0.1)",
              }}
            >
              {rec.target_price >= rec.price ? "+" : ""}
              {(((rec.target_price - rec.price) / rec.price) * 100).toFixed(1)}%
            </span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/* ── Main Page ── */
export default function MatchmakerPage() {
  const { items } = usePortfolio();
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [started, setStarted] = useState(false);
  const [error, setError] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [liked, setLiked] = useState<Recommendation[]>([]);
  const [passed, setPassed] = useState<string[]>([]);
  const [addedToWatchlist, setAddedToWatchlist] = useState<Set<string>>(new Set());

  const fetchRecommendations = async (refresh = false) => {
    setLoading(true);
    setStarted(true);
    setError("");
    setCurrentIndex(0);
    setLiked([]);
    setPassed([]);
    setAddedToWatchlist(new Set());
    try {
      const tickers = items.map((i) => i.ticker);
      // Fetch current watchlist to exclude those tickers
      let watchlist: string[] = [];
      try {
        const wlRes = await api.get("/api/watchlist");
        watchlist = (wlRes.data?.items || []).map((w: { ticker: string }) => w.ticker);
      } catch {}
      const { data } = await api.post("/api/ai/matchmaker", { tickers, watchlist, refresh });
      const recs: Recommendation[] = data.recommendations || [];
      if (recs.length === 0) {
        setError("AI could not generate recommendations. Please try again.");
      }
      setRecommendations(recs);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to fetch recommendations";
      setError(msg);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = async (ticker: string) => {
    try {
      await api.post("/api/watchlist", { ticker });
      setAddedToWatchlist((prev) => new Set([...prev, ticker]));
    } catch {
      // Probably already in watchlist
      setAddedToWatchlist((prev) => new Set([...prev, ticker]));
    }
  };

  const handleSwipeRight = useCallback(() => {
    const rec = recommendations[currentIndex];
    if (!rec) return;
    setLiked((prev) => [...prev, rec]);
    addToWatchlist(rec.ticker);
    setCurrentIndex((i) => i + 1);
  }, [currentIndex, recommendations]);

  const handleSwipeLeft = useCallback(() => {
    const rec = recommendations[currentIndex];
    if (!rec) return;
    setPassed((prev) => [...prev, rec.ticker]);
    setCurrentIndex((i) => i + 1);
  }, [currentIndex, recommendations]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!started || loading || currentIndex >= recommendations.length) return;
      if (e.key === "ArrowRight") handleSwipeRight();
      if (e.key === "ArrowLeft") handleSwipeLeft();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [started, loading, currentIndex, recommendations.length, handleSwipeRight, handleSwipeLeft]);

  const isDone = started && !loading && !error && currentIndex >= recommendations.length && recommendations.length > 0;
  const remaining = recommendations.length - currentIndex;

  return (
    <ProGate>
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-2xl font-black tracking-wide flex items-center gap-3" style={{ color: "var(--text-primary)" }}>
              <Heart className="text-[#FF2D55]" size={24} />
              AI Matchmaker
            </h1>
            <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
              Swipe right to add to watchlist
            </p>
          </div>
          {started && !loading && (
            <div className="flex items-center gap-2">
              {remaining > 0 && (
                <span className="text-xs font-bold tabular-nums" style={{ color: "var(--text-dim)" }}>
                  {currentIndex + 1}/{recommendations.length}
                </span>
              )}
              <button
                onClick={() => fetchRecommendations(true)}
                className="flex items-center gap-2 px-3 py-1.5 border font-bold rounded-xl text-xs transition-colors hover:bg-white/5"
                style={{ borderColor: "var(--border-default)", color: "var(--text-secondary)" }}
              >
                <RotateCcw size={12} />
                New
              </button>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {started && !loading && !error && recommendations.length > 0 && !isDone && (
          <div className="w-full h-1 rounded-full mb-5 overflow-hidden" style={{ background: "var(--input-bg)" }}>
            <div
              className="h-full rounded-full bg-[#FF2D55] transition-all duration-300"
              style={{ width: `${(currentIndex / recommendations.length) * 100}%` }}
            />
          </div>
        )}

        {!started ? (
          /* ── Start Screen ── */
          <div className="border rounded-3xl p-12 text-center relative overflow-hidden" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[300px] h-[200px] rounded-full blur-[100px] bg-[#FF2D55]/10 pointer-events-none" />
            <Sparkles className="w-16 h-16 text-[#FF2D55] mx-auto mb-5" />
            <h2 className="text-xl font-black mb-3" style={{ color: "var(--text-primary)" }}>Find Your Next Stock</h2>
            <p className="text-sm max-w-sm mx-auto mb-6" style={{ color: "var(--text-muted)" }}>
              Swipe right on stocks you like — they'll be added to your watchlist automatically.
            </p>
            <button
              onClick={() => fetchRecommendations(false)}
              disabled={loading}
              className="inline-flex items-center gap-2 px-8 py-3 bg-[#FF2D55] text-white font-black rounded-xl hover:bg-[#e0274d] transition-colors"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Heart size={18} />}
              Start Matching
            </button>
          </div>
        ) : loading ? (
          /* ── Loading ── */
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#FF2D55]" />
            <p className="text-sm font-bold" style={{ color: "var(--text-muted)" }}>AI is analyzing your portfolio...</p>
            <p className="text-xs" style={{ color: "var(--text-dim)" }}>Finding 10 stocks that match your style</p>
          </div>
        ) : error ? (
          /* ── Error ── */
          <div className="border rounded-3xl p-8 text-center" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
            <Heart className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h2 className="text-lg font-bold mb-3" style={{ color: "var(--text-primary)" }}>Something went wrong</h2>
            <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>{error}</p>
            <button
              onClick={() => fetchRecommendations(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#FF2D55] text-white font-bold rounded-xl hover:bg-[#e0274d]"
            >
              <RotateCcw size={14} />
              Try Again
            </button>
          </div>
        ) : isDone ? (
          /* ── Done — Summary ── */
          <div className="border rounded-3xl p-8 text-center" style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}>
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="text-xl font-black mb-2" style={{ color: "var(--text-primary)" }}>All Done!</h2>
            <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
              You liked <span className="text-[#32D74B] font-black">{liked.length}</span> and passed on <span className="text-[#FF453A] font-black">{passed.length}</span> stocks
            </p>

            {/* Liked stocks list */}
            {liked.length > 0 && (
              <div className="mb-6">
                <p className="text-xs font-bold mb-3 text-left" style={{ color: "var(--text-dim)" }}>ADDED TO WATCHLIST</p>
                <div className="space-y-2">
                  {liked.map((rec) => (
                    <div
                      key={rec.ticker}
                      className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-left"
                      style={{ background: "var(--bg-surface)" }}
                    >
                      <StockLogo ticker={rec.ticker} size={32} />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-black" style={{ color: "var(--text-primary)" }}>{rec.ticker}</span>
                        <span className="text-xs ml-2" style={{ color: "var(--text-muted)" }}>{rec.name}</span>
                      </div>
                      {rec.price && rec.price > 0 && (
                        <span className="text-sm font-bold tabular-nums" style={{ color: "var(--text-primary)" }}>
                          ${rec.price.toFixed(2)}
                        </span>
                      )}
                      <Check size={14} className="text-[#32D74B]" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => fetchRecommendations(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#FF2D55] text-white font-black rounded-xl hover:bg-[#e0274d]"
            >
              <RotateCcw size={14} />
              Find More Matches
            </button>
          </div>
        ) : (
          /* ── Swipe Cards ── */
          <>
            <div className="relative w-full" style={{ height: 560 }}>
              {/* Stack: show current + next card behind */}
              {recommendations.slice(currentIndex, currentIndex + 2).reverse().map((rec, stackIdx) => {
                const isTop = stackIdx === (Math.min(2, recommendations.length - currentIndex) - 1);
                return (
                  <SwipeCard
                    key={rec.ticker + "-" + currentIndex}
                    rec={rec}
                    onSwipeRight={handleSwipeRight}
                    onSwipeLeft={handleSwipeLeft}
                    isTop={isTop}
                  />
                );
              })}
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-center gap-6 mt-5">
              <button
                onClick={handleSwipeLeft}
                className="w-16 h-16 rounded-full border-2 flex items-center justify-center transition-all hover:scale-110 hover:border-[#FF453A] hover:bg-[#FF453A]/10 active:scale-95"
                style={{ borderColor: "var(--border-default)", color: "#FF453A" }}
              >
                <X size={28} />
              </button>

              <div className="flex flex-col items-center gap-0.5">
                <span className="text-[9px] font-bold" style={{ color: "var(--text-dim)" }}>
                  <ChevronLeft size={10} className="inline" /> swipe <ChevronRight size={10} className="inline" />
                </span>
              </div>

              <button
                onClick={handleSwipeRight}
                className="w-16 h-16 rounded-full border-2 flex items-center justify-center transition-all hover:scale-110 hover:border-[#32D74B] hover:bg-[#32D74B]/10 active:scale-95"
                style={{ borderColor: "var(--border-default)", color: "#32D74B" }}
              >
                <Heart size={28} />
              </button>
            </div>

            {/* Keyboard hint */}
            <p className="text-center text-[10px] mt-3" style={{ color: "var(--text-dim)" }}>
              or use ← → arrow keys
            </p>

            {/* Mini summary bar */}
            {(liked.length > 0 || passed.length > 0) && (
              <div className="flex items-center justify-center gap-4 mt-4">
                <span className="text-xs font-bold flex items-center gap-1" style={{ color: "#32D74B" }}>
                  <Heart size={10} fill="#32D74B" /> {liked.length} liked
                </span>
                <span className="text-xs font-bold flex items-center gap-1" style={{ color: "#FF453A" }}>
                  <X size={10} /> {passed.length} passed
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </ProGate>
  );
}
