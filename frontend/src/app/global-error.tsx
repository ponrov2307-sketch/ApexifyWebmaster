"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="bg-[#080B10] text-white min-h-screen flex items-center justify-center">
        <div className="text-center p-10">
          <h2 className="text-2xl font-black mb-4">Something went wrong</h2>
          <p className="text-gray-400 mb-6">{error.message}</p>
          <button
            onClick={reset}
            className="px-6 py-3 bg-[#D0FD3E] text-black font-bold rounded-xl"
          >
            Try Again
          </button>
        </div>
      </body>
    </html>
  );
}
