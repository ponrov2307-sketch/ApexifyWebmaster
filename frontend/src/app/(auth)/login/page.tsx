"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-store";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import Image from "next/image";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, tokenLogin } = useAuth();

  const [telegramId, setTelegramId] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Auto token-login from URL param
  const tokenParam = searchParams.get("token");
  useEffect(() => {
    if (!tokenParam) return;
    setLoading(true);
    tokenLogin(tokenParam)
      .then(() => router.replace("/"))
      .catch(() => {
        setError("Token login failed — please sign in manually.");
        setLoading(false);
      });
  }, [tokenParam, tokenLogin, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!telegramId.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }
    setLoading(true);
    try {
      await login(telegramId.trim(), password.trim());
      router.replace("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Login failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080B10] relative overflow-hidden">
      {/* Atmospheric glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[420px] rounded-full blur-[140px] bg-[#D0FD3E]/7 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[450px] h-[450px] rounded-full blur-[110px] bg-[#00BFFF]/5 pointer-events-none" />
      <div className="absolute top-1/3 right-0 w-[350px] h-[350px] rounded-full blur-[110px] bg-[#AF52DE]/4 pointer-events-none" />

      <div className="w-[94vw] max-w-[420px] bg-[#0D1117] rounded-3xl overflow-hidden relative shadow-[0_0_0_1px_rgba(208,253,62,0.15),0_50px_100px_rgba(0,0,0,0.8)]">
        {/* Top accent line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#D0FD3E]/50 to-transparent" />
        {/* Inner top glow */}
        <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-[280px] h-[160px] rounded-full blur-[50px] bg-[#D0FD3E]/8 pointer-events-none" />

        <form
          onSubmit={handleLogin}
          className="relative z-10 p-9 flex flex-col items-center gap-0"
        >
          {/* Logo */}
          <div className="relative w-20 h-20 mb-2">
            <Image
              src="/apexify-logo.png"
              alt="Apexify"
              fill
              className="rounded-full object-contain shadow-[0_0_30px_rgba(208,253,62,0.15)]"
              priority
              onError={(e) => {
                (e.target as HTMLElement).style.display = "none";
              }}
            />
          </div>

          <h1 className="text-[2rem] font-black tracking-[0.35em] text-white leading-none">
            APEXIFY
          </h1>
          <p className="text-[9px] font-bold tracking-[0.4em] text-[#D0FD3E]/50 mt-1">
            PORTFOLIO DASHBOARD
          </p>

          <div className="w-14 h-px bg-gradient-to-r from-transparent via-[#D0FD3E]/30 to-transparent my-5" />

          <p className="text-gray-500 text-[13px] mb-5 text-center">
            Sign in with your Telegram account
          </p>

          {/* Telegram ID */}
          <div className="w-full mb-3">
            <input
              type="text"
              inputMode="numeric"
              placeholder="Telegram ID"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40 focus:ring-1 focus:ring-[#D0FD3E]/20 transition-all"
            />
          </div>

          {/* Password */}
          <div className="w-full mb-3 relative">
            <input
              type={showPwd ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-600 outline-none focus:border-[#D0FD3E]/40 focus:ring-1 focus:ring-[#D0FD3E]/20 transition-all pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPwd(!showPwd)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
            >
              {showPwd ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {/* Hints */}
          <div className="w-full flex justify-between items-start mb-5 gap-1">
            <span className="text-[11px] text-[#FCD535]/60 leading-snug max-w-[60%]">
              Use the secure passcode from admin.
            </span>
            <span className="text-[11px] text-[#00BFFF]/60 text-right">
              หรือเปิดจาก Telegram bot
            </span>
          </div>

          {/* Error */}
          {error && (
            <div className="w-full mb-4 p-3 bg-[#FF453A]/10 border border-[#FF453A]/30 rounded-xl text-[#FF453A] text-sm text-center">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-[#D0FD3E] hover:bg-[#c5f232] text-[#080B10] font-black tracking-[0.2em] text-sm rounded-xl transition-all shadow-[0_0_20px_rgba(208,253,62,0.3)] hover:shadow-[0_0_30px_rgba(208,253,62,0.45)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              "SIGN IN"
            )}
          </button>

          <p className="text-[10px] text-gray-700 mt-6 tracking-[0.25em]">
            APEXIFY &copy; 2025
          </p>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#080B10]">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
