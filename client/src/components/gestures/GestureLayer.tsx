/**
 * 全域手勢層
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * - 單指右滑 → 繼續生成
 * - 單指左滑 → 撤回
 * - 邊緣右滑 → 設定
 * - 邊緣左滑 → 歷史
 * - 雙指縮放 → 字體
 * - 三指點擊 → 緊急回報
 * - 長按訊息：由訊息節點 data-monster-msg 自行處理
 */
import { useEffect, useRef } from "react";
import { useLocation } from "wouter";
import { useGestures } from "@/contexts/GestureContext";
import { toast } from "sonner";

const EDGE = 28;

export default function GestureLayer() {
  const {
    enabled,
    pauseOnInputFocus,
    inputFocused,
    handlers,
    thresholdPx,
    leftHanded,
    fontScale,
    setFontScale,
  } = useGestures();
  const [, setLocation] = useLocation();
  const start = useRef<{ x: number; y: number; t: number; fingers: number } | null>(null);
  const pinch0 = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const paused = pauseOnInputFocus && inputFocused;

    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 3) {
        handlers.emergency_feedback?.();
        window.dispatchEvent(new CustomEvent("monster:emergency-feedback"));
        toast.message("緊急回報");
        return;
      }
      if (e.touches.length === 2) {
        const a = e.touches[0];
        const b = e.touches[1];
        pinch0.current = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
        return;
      }
      if (e.touches.length !== 1 || paused) return;
      const t = e.touches[0];
      start.current = { x: t.clientX, y: t.clientY, t: Date.now(), fingers: 1 };
    };

    const onTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && pinch0.current) {
        const a = e.touches[0];
        const b = e.touches[1];
        const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
        const ratio = d / pinch0.current;
        if (Math.abs(ratio - 1) > 0.08) {
          const next = Math.min(1.4, Math.max(0.85, fontScale * (ratio > 1 ? 1.02 : 0.98)));
          setFontScale(next);
          handlers.font_zoom?.();
          pinch0.current = d;
        }
      }
    };

    const onTouchEnd = (e: TouchEvent) => {
      pinch0.current = null;
      if (!start.current || paused) {
        start.current = null;
        return;
      }
      const t = e.changedTouches[0];
      if (!t) return;
      const dx = t.clientX - start.current.x;
      const dy = t.clientY - start.current.y;
      const absX = Math.abs(dx);
      const absY = Math.abs(dy);
      const fromLeft = start.current.x <= EDGE;
      const fromRight = start.current.x >= window.innerWidth - EDGE;
      start.current = null;

      if (absX < thresholdPx || absX < absY * 1.2) return;

      const swipeRight = leftHanded ? dx < 0 : dx > 0;
      const swipeLeft = leftHanded ? dx > 0 : dx < 0;

      if (fromLeft && swipeRight) {
        handlers.open_history?.();
        setLocation("/");
        toast.message("歷史");
        return;
      }
      if (fromRight && swipeLeft) {
        handlers.open_settings?.();
        setLocation("/settings");
        toast.message("設定");
        return;
      }
      if (swipeRight) {
        handlers.continue_generate?.();
        window.dispatchEvent(new CustomEvent("monster:gesture-continue"));
      } else if (swipeLeft) {
        handlers.undo?.();
        window.dispatchEvent(new CustomEvent("monster:gesture-undo"));
      }
    };

    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    window.addEventListener("touchend", onTouchEnd, { passive: true });
    return () => {
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("touchend", onTouchEnd);
    };
  }, [
    enabled,
    pauseOnInputFocus,
    inputFocused,
    handlers,
    thresholdPx,
    leftHanded,
    fontScale,
    setFontScale,
    setLocation,
  ]);

  return null;
}
