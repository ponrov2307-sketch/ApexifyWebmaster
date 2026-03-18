export function fmt(n: number) {
  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function fmtPct(n: number) {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

export function logoUrl(ticker: string): string {
  // Use our backend proxy which fetches from TradingView/Yahoo with proper headers
  return `/api/market/logo/${encodeURIComponent(ticker.toUpperCase())}`;
}

export interface TradePlan {
  ticker: string;
  action: string;
  signal: string;
  reason: string;
  entryLow: number;
  entryHigh: number;
  sl: number;
  tp1: number;
  tp2: number;
  rr: number;
  confidence: number;
  pnl_pct: number;
}

export function buildTradePlan(asset: { ticker: string; price: number; avg_cost: number; pnl_pct: number; sparkline: number[] }): TradePlan {
  const { ticker, price, avg_cost, pnl_pct, sparkline } = asset;
  const trendUp = sparkline && sparkline.length > 1 ? sparkline[sparkline.length - 1] >= sparkline[0] : price >= avg_cost;
  let action: string, signal: string, reason: string;

  if (pnl_pct >= 15) {
    action = "TAKE PROFIT"; signal = "SELL-TRIM";
    reason = "Profit extended — scale out gradually.";
  } else if (pnl_pct <= -8) {
    action = "CUT LOSS"; signal = "SELL-REDUCE";
    reason = "Loss exceeded threshold — control downside risk.";
  } else if (pnl_pct < 5) {
    action = "WATCH"; signal = "WAIT";
    reason = "Range-bound — watch for confirmation.";
  } else {
    action = "HOLD"; signal = trendUp ? "BUY-ON-DIP" : "HOLD";
    reason = "Momentum constructive — continue holding.";
  }

  const cp = price > 0 ? price : (avg_cost > 0 ? avg_cost : 1);
  const entryLow = cp * (trendUp ? 0.98 : 0.965);
  const entryHigh = cp * (trendUp ? 1.01 : 0.99);
  const sl = cp * (trendUp ? 0.94 : 0.92);
  const tp1 = cp * (trendUp ? 1.08 : 1.06);
  const tp2 = cp * (trendUp ? 1.14 : 1.1);
  const rr = Math.max((tp1 - entryHigh), 0.01) / Math.max((entryHigh - sl), 0.01);

  let confidence = 55;
  if (trendUp) confidence += 12;
  if (action === "HOLD") confidence += 8;
  if (action === "TAKE PROFIT") confidence += 5;
  if (action === "CUT LOSS" || action === "WATCH") confidence -= 10;
  if (rr >= 2) confidence += 8;
  else if (rr < 1) confidence -= 12;
  confidence = Math.max(20, Math.min(92, Math.round(confidence)));

  return { ticker, action, signal, reason, entryLow, entryHigh, sl, tp1, tp2, rr, confidence, pnl_pct };
}

export interface HealthScore {
  score: number;
  subscores: { Concentration: number; Drawdown: number; Volatility: number; Correlation: number };
  issues: string[];
  actions: string[];
}

export function computeHealthScore(items: { value: number; pnl_pct: number }[]): HealthScore {
  if (!items.length) return { score: 0, subscores: { Concentration: 0, Drawdown: 0, Volatility: 0, Correlation: 0 }, issues: ["No holdings"], actions: ["Add stocks to your portfolio"] };
  const total = items.reduce((s, i) => s + Math.max(i.value, 0), 0);
  if (total <= 0) return { score: 0, subscores: { Concentration: 0, Drawdown: 0, Volatility: 0, Correlation: 0 }, issues: ["Zero value portfolio"], actions: ["Check your holdings"] };
  const weights = items.map(i => Math.max(i.value, 0) / total);
  const maxW = Math.max(...weights);
  const top3W = [...weights].sort((a, b) => b - a).slice(0, 3).reduce((s, w) => s + w, 0);
  const pnlPcts = items.map(i => i.pnl_pct);
  const lossExposure = weights.reduce((s, w, i) => s + (pnlPcts[i] < 0 ? w : 0), 0);
  const negPcts = pnlPcts.filter(p => p < 0);
  const avgLossMag = negPcts.length ? Math.abs(negPcts.reduce((s, p) => s + p, 0) / negPcts.length) : 0;
  const weightedDownside = weights.reduce((s, w, i) => s + Math.max(-pnlPcts[i], 0) * w, 0);

  const concPen = Math.min(Math.max((maxW - 0.50) * 100 * 0.55, 0), 25);
  const ddPen = Math.min(Math.max((lossExposure - 0.50) * 100 * 0.22, 0) + Math.max(avgLossMag - 12, 0) * 0.22, 20);
  const volPen = Math.min(Math.max(weightedDownside - 9, 0) * 0.6, 15);
  const corrPen = Math.min(Math.max((top3W - 0.78) * 100 * 0.42, 0), 15);
  const score = Math.max(20, Math.round(100 - concPen - ddPen - volPen - corrPen));

  const sub = (pen: number, cap: number) => Math.max(0, Math.min(100, Math.round(100 - (pen / cap) * 100)));
  const subscores = { Concentration: sub(concPen, 25), Drawdown: sub(ddPen, 20), Volatility: sub(volPen, 15), Correlation: sub(corrPen, 15) };

  const issues: string[] = [];
  const actions: string[] = [];
  if (maxW > 0.45) { issues.push(`Top holding is ${(maxW * 100).toFixed(0)}% of portfolio`); actions.push("Diversify across more assets"); }
  if (lossExposure > 0.50) { issues.push(`${(lossExposure * 100).toFixed(0)}% of portfolio is in loss`); actions.push("Review losing positions"); }
  if (weightedDownside > 9) { issues.push("High weighted downside volatility"); actions.push("Reduce exposure to volatile assets"); }
  if (top3W > 0.78) { issues.push(`Top 3 holdings are ${(top3W * 100).toFixed(0)}% of portfolio`); actions.push("Spread risk across more sectors"); }
  if (!issues.length) { issues.push("Portfolio is well-balanced"); actions.push("Continue current strategy"); }

  return { score, subscores, issues, actions };
}

export const ACTION_THEME: Record<string, { text: string; bg: string }> = {
  "TAKE PROFIT": { text: "text-[#32D74B]", bg: "bg-[#32D74B]/10 border-[#32D74B]/30" },
  "CUT LOSS": { text: "text-[#FF453A]", bg: "bg-[#FF453A]/10 border-[#FF453A]/30" },
  WATCH: { text: "text-[#FCD535]", bg: "bg-[#FCD535]/10 border-[#FCD535]/30" },
  HOLD: { text: "text-[#8AB4FF]", bg: "bg-[#8AB4FF]/10 border-[#8AB4FF]/30" },
};
