"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang, tr } from "@/lib/i18n";
import { Bot, X, Send, Loader2 } from "lucide-react";
import api from "@/lib/api";

export default function CopilotFab() {
  const user = useAuth((s) => s.user);
  const { lang } = useLang();
  const role = user?.role?.toLowerCase() || "free";
  const isPro = ["pro", "admin"].includes(role);

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<
    { role: "user" | "ai"; text: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const send = async () => {
    if (sending || !input.trim()) return;
    const q = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setSending(true);
    try {
      const { data } = await api.post("/api/ai/copilot", { message: q });
      setMessages((m) => [
        ...m,
        { role: "ai", text: data.reply || "No response" },
      ]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: lang === "TH" ? "ไม่สามารถเชื่อมต่อ AI ได้" : "AI unavailable" }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      {/* Dialog */}
      {open && (
        <div className="fixed bottom-20 right-5 z-[1200] w-[92vw] max-w-[420px] h-[68vh] max-h-[640px] bg-[#0B1320]/95 border border-[#39C8FF]/30 rounded-3xl overflow-hidden shadow-2xl flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span className="text-sm font-black tracking-widest text-[#39C8FF]">
              {tr("copilot.title", lang)}
            </span>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-400 hover:text-white p-1"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-3 space-y-2"
          >
            {!isPro ? (
              <div className="text-sm text-gray-300 p-3">
                <p className="mb-3">
                  Copilot is a Pro feature. Upgrade to unlock AI-powered
                  portfolio insights.
                </p>
                <button
                  onClick={() => (window.location.href = "/payment")}
                  className="w-full bg-[#FCD535] text-black font-black rounded-xl py-2"
                >
                  {tr("copilot.upgrade_btn", lang)}
                </button>
              </div>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={`text-sm rounded-xl p-2 ${
                    m.role === "user"
                      ? "text-white bg-white/5"
                      : "text-gray-100 bg-[#39C8FF]/10 border border-[#39C8FF]/20"
                  }`}
                >
                  <strong>{m.role === "user" ? "You:" : "Copilot:"}</strong>{" "}
                  {m.text}
                </div>
              ))
            )}
            {sending && (
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Loader2 size={14} className="animate-spin text-[#39C8FF]" />
                Thinking...
              </div>
            )}
          </div>

          {/* Input */}
          {isPro && (
            <div className="p-3 border-t border-white/10 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder={tr("copilot.placeholder", lang)}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm outline-none focus:border-[#39C8FF]/40"
              />
              <button
                onClick={send}
                disabled={sending}
                className="bg-[#20D6A1] text-black font-black rounded-xl px-4 py-2 disabled:opacity-50"
              >
                <Send size={16} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* FAB */}
      <div className="fixed bottom-5 right-5 z-[1200]">
        <button
          onClick={() => setOpen(!open)}
          className={`${
            isPro
              ? "bg-[#20D6A1] text-black hover:scale-105"
              : "bg-[#FCD535] text-black hover:scale-105"
          } rounded-full px-5 py-3 font-black shadow-[0_12px_30px_rgba(0,0,0,0.45)] transition-transform flex items-center gap-2`}
        >
          <Bot size={20} />
          {tr("copilot.fab", lang)}
        </button>
      </div>
    </>
  );
}
