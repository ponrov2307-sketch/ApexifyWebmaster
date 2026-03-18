"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-store";
import { Loader2 } from "lucide-react";

function LoginTokenHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, tokenLogin } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");
    const telegramId =
      searchParams.get("telegram_id") || searchParams.get("tid");
    const password =
      searchParams.get("password") ||
      searchParams.get("passcode") ||
      searchParams.get("pwd");

    async function doLogin() {
      try {
        if (token) {
          await tokenLogin(token);
        } else if (telegramId && password) {
          await login(telegramId, password);
        } else {
          router.replace("/login");
          return;
        }
        router.replace("/");
      } catch {
        router.replace("/login");
      }
    }

    doLogin();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080B10]">
      <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
    </div>
  );
}

export default function LoginTokenPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#080B10]">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      }
    >
      <LoginTokenHandler />
    </Suspense>
  );
}
