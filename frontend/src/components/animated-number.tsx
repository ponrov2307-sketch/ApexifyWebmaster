"use client";

import { useEffect, useRef, useState, useCallback, memo } from "react";

/**
 * AnimatedNumber — smooth counting + flash on change
 *
 * Features:
 *   - 60fps requestAnimationFrame interpolation
 *   - Green/red flash when value changes
 *   - Configurable duration, format, prefix/suffix
 *   - Tabular nums for alignment
 */

interface AnimatedNumberProps {
  value: number;
  /** Format function, e.g. fmt or (n) => n.toFixed(2) */
  format?: (n: number) => string;
  /** Prefix like "$" or "฿" */
  prefix?: string;
  /** Suffix like "%" */
  suffix?: string;
  /** Animation duration in ms (default 600) */
  duration?: number;
  /** Show directional flash: green up / red down (default true) */
  flash?: boolean;
  /** Extra className */
  className?: string;
  /** Style passthrough */
  style?: React.CSSProperties;
  /** Color to use for positive flash (default #32D74B) */
  positiveColor?: string;
  /** Color to use for negative flash (default #FF453A) */
  negativeColor?: string;
}

// Easing: ease-out cubic
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

function AnimatedNumberInner({
  value,
  format = (n) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
  prefix = "",
  suffix = "",
  duration = 600,
  flash = true,
  className = "",
  style,
  positiveColor = "#32D74B",
  negativeColor = "#FF453A",
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(format(value));
  const [flashDir, setFlashDir] = useState<"up" | "down" | null>(null);

  const prevValue = useRef(value);
  const rafRef = useRef<number>(0);
  const startRef = useRef(0);
  const fromRef = useRef(value);
  const toRef = useRef(value);
  const mountedRef = useRef(false);

  const animate = useCallback(() => {
    const now = performance.now();
    const elapsed = now - startRef.current;
    const progress = Math.min(elapsed / duration, 1);
    const eased = easeOutCubic(progress);

    const current = fromRef.current + (toRef.current - fromRef.current) * eased;
    setDisplay(format(current));

    if (progress < 1) {
      rafRef.current = requestAnimationFrame(animate);
    }
  }, [duration, format]);

  useEffect(() => {
    // Skip animation on first render
    if (!mountedRef.current) {
      mountedRef.current = true;
      prevValue.current = value;
      setDisplay(format(value));
      return;
    }

    const prev = prevValue.current;
    if (prev === value) return;

    // Flash direction
    if (flash) {
      const dir = value > prev ? "up" : "down";
      setFlashDir(dir);
      const timer = setTimeout(() => setFlashDir(null), 800);
      // Cleanup
      prevValue.current = value;

      // Start animation
      cancelAnimationFrame(rafRef.current);
      fromRef.current = prev;
      toRef.current = value;
      startRef.current = performance.now();
      rafRef.current = requestAnimationFrame(animate);

      return () => {
        clearTimeout(timer);
        cancelAnimationFrame(rafRef.current);
      };
    }

    prevValue.current = value;
    cancelAnimationFrame(rafRef.current);
    fromRef.current = prev;
    toRef.current = value;
    startRef.current = performance.now();
    rafRef.current = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(rafRef.current);
  }, [value, flash, animate, format]);

  // Flash glow styles
  const flashStyle: React.CSSProperties = flashDir
    ? {
        textShadow:
          flashDir === "up"
            ? `0 0 12px ${positiveColor}60, 0 0 4px ${positiveColor}30`
            : `0 0 12px ${negativeColor}60, 0 0 4px ${negativeColor}30`,
        transition: "text-shadow 0.3s ease-out",
      }
    : { textShadow: "none", transition: "text-shadow 0.8s ease-out" };

  return (
    <span
      className={`tabular-nums inline-block ${className}`}
      style={{ ...style, ...flashStyle }}
    >
      {prefix}{display}{suffix}
    </span>
  );
}

export const AnimatedNumber = memo(AnimatedNumberInner);
export default AnimatedNumber;
