"use client";

import { useState } from "react";
import { useLang, tr } from "@/lib/i18n";
import api from "@/lib/api";
import Markdown from "react-markdown";
import ProGate from "@/components/pro-gate";
import { Sun, Loader2, RefreshCw, Sparkles } from "lucide-react";

export default function MorningBriefingPage() {
  const { lang } = useLang();
  const [loading, setLoading] = useState(false);
  const [briefing, setBriefing] = useState<string | null>(null);
  const [error, setError] = useState("");

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/api/ai/morning-briefing");
      setBriefing(data.briefing || "No briefing available");
    } catch {
      setError(lang === "TH" ? "ไม่สามารถสร้างสรุปได้" : "Failed to generate briefing");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProGate>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-black text-white tracking-wide flex items-center gap-3">
            <Sun className="text-[#FCD535]" size={24} />
            {tr("morning.title", lang)}
          </h1>
          <p className="text-gray-500 text-sm mt-1">{tr("morning.subtitle", lang)}</p>
        </div>

        {!briefing && !loading && !error ? (
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-12 text-center relative overflow-hidden">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[300px] h-[200px] rounded-full blur-[100px] bg-[#FCD535]/10 pointer-events-none" />
            <Sparkles className="w-16 h-16 text-[#FCD535] mx-auto mb-5" />
            <h2 className="text-xl font-black text-white mb-3">
              {lang === "TH" ? "พร้อมเริ่มวันใหม่?" : "Ready to Start Your Day?"}
            </h2>
            <p className="text-gray-400 text-sm max-w-sm mx-auto mb-6">
              {lang === "TH"
                ? "AI จะวิเคราะห์สภาพตลาด Fear & Greed, VIX และ Sector Flow เพื่อสรุปให้คุณ"
                : "AI analyzes market conditions, Fear & Greed, VIX, and Sector Flow for your daily summary"}
            </p>
            <button
              onClick={generate}
              className="inline-flex items-center gap-2 px-8 py-3 bg-[#FCD535] text-black font-black rounded-xl hover:bg-[#e5c130] transition-colors"
            >
              <Sun size={18} />
              {tr("morning.generate", lang)}
            </button>
          </div>
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-2 border-[#FCD535]/20 border-t-[#FCD535] animate-spin" />
              <Sun size={24} className="text-[#FCD535] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="text-gray-400 text-sm font-bold">
              {lang === "TH" ? "AI กำลังสรุปตลาดให้คุณ..." : "AI is summarizing the market..."}
            </p>
            <p className="text-gray-600 text-xs">
              {lang === "TH" ? "อาจใช้เวลา 10-20 วินาที" : "This may take 10-20 seconds"}
            </p>
          </div>
        ) : error ? (
          <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-8 text-center">
            <Sun className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">{error}</p>
            <button onClick={generate}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#FCD535] text-black font-bold rounded-xl">
              <RefreshCw size={14} /> {tr("common.try_again", lang)}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-[#0D1117] border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sun size={16} className="text-[#FCD535]" />
                  <span className="text-sm font-black text-white">
                    {new Date().toLocaleDateString(lang === "TH" ? "th-TH" : "en-US", {
                      weekday: "long", year: "numeric", month: "long", day: "numeric"
                    })}
                  </span>
                </div>
                <span className="text-[10px] text-[#FCD535] font-bold bg-[#FCD535]/10 px-2 py-1 rounded-full">
                  Powered by Gemini AI
                </span>
              </div>
              <div className="p-6">
                <Markdown components={{
                  h2: ({ children }) => <h2 className="text-lg font-black text-white mt-4 mb-3 tracking-wide">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-base font-bold text-gray-200 mt-3 mb-2">{children}</h3>,
                  p: ({ children }) => <p className="text-gray-300 leading-relaxed text-sm mb-2">{children}</p>,
                  ul: ({ children }) => <ul className="space-y-1.5 mb-3">{children}</ul>,
                  li: ({ children }) => <li className="text-gray-300 text-sm flex gap-2"><span className="shrink-0">•</span><span>{children}</span></li>,
                  strong: ({ children }) => <strong className="text-white font-bold">{children}</strong>,
                }}>{briefing || ""}</Markdown>
              </div>
            </div>

            <button onClick={generate}
              className="w-full py-3 bg-white/5 border border-white/10 text-gray-300 font-bold rounded-xl hover:bg-white/10 transition-colors text-sm flex items-center justify-center gap-2">
              <RefreshCw size={14} /> {tr("morning.regenerate", lang)}
            </button>
          </div>
        )}
      </div>
    </ProGate>
  );
}
