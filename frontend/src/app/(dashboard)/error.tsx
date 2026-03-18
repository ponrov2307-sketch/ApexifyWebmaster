"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="bg-[#0D1117] border border-white/8 rounded-2xl p-10 text-center max-w-md">
        <div className="w-16 h-16 rounded-2xl bg-[#FF453A]/10 border border-[#FF453A]/20 flex items-center justify-center mx-auto mb-5">
          <AlertTriangle className="text-[#FF453A]" size={28} />
        </div>
        <h2 className="text-xl font-black text-white mb-2">Something went wrong</h2>
        <p className="text-gray-400 text-sm mb-6 leading-relaxed">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 text-gray-300 font-bold rounded-xl hover:bg-white/10 transition-colors"
        >
          <RotateCcw size={14} />
          Try Again
        </button>
      </div>
    </div>
  );
}
