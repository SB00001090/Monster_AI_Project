/**
 * 公測訪客 UI 殼：標籤、額度、水印、一鍵 Bug 回報
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useState } from "react";
import { Bug, Sparkles } from "lucide-react";
import { useGuest } from "@/contexts/GuestContext";
import BugReportModal from "@/components/BugReportModal";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** 右上角公測標籤 + 額度條 */
export function PublicBetaBadge({ className }: { className?: string }) {
  const { isGuest, isPublicBeta, badgeLabel, quota, publisher } = useGuest();
  if (!isPublicBeta && !isGuest) return null;

  return (
    <div
      className={cn(
        "pointer-events-none fixed top-3 left-1/2 z-[60] -translate-x-1/2 flex flex-col items-center gap-1",
        className,
      )}
      role="status"
      aria-label={badgeLabel}
    >
      <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-pink-500/50 bg-black/70 px-3 py-1 text-xs font-semibold text-pink-300 shadow-[0_0_12px_rgba(255,77,154,0.35)] backdrop-blur">
        <Sparkles className="h-3.5 w-3.5 text-cyan-300" />
        <span>{badgeLabel}</span>
        <span className="text-[10px] text-white/50">· {publisher}</span>
      </div>
      <div className="pointer-events-auto rounded-md border border-cyan-500/30 bg-black/60 px-2 py-0.5 text-[10px] text-cyan-200/90 backdrop-blur">
        {import.meta.env.VITE_UNLIMITED_MODE === "false"
          ? `RP ${quota.rpRemaining}/${quota.rpLimit} · 圖像 ${quota.imageRemaining}/${quota.imageLimit}`
          : "無限額 · 無審查 RP"}
      </div>
    </div>
  );
}

/** 右下角半透明水印（無法關閉 — 公測訪客） */
export function PublicBetaWatermark() {
  const { isGuest, isPublicBeta, watermarkText } = useGuest();
  if (!isPublicBeta && !isGuest) return null;

  return (
    <div
      className="pointer-events-none fixed bottom-3 right-3 z-[55] select-none text-[11px] text-white/40"
      aria-hidden
    >
      {watermarkText}
    </div>
  );
}

/** 一鍵 Bug 回報 FAB（沿用 BugReportModal） */
export function PublicBetaBugFab() {
  const { isGuest, isPublicBeta } = useGuest();
  const [open, setOpen] = useState(false);
  if (!isPublicBeta && !isGuest) return null;

  return (
    <>
      <Button
        type="button"
        size="sm"
        onClick={() => setOpen(true)}
        className="fixed bottom-16 right-3 z-[56] h-10 gap-1.5 rounded-full border border-cyan-400/40 bg-cyan-500/20 px-3 text-cyan-100 shadow-[0_0_16px_rgba(0,229,255,0.25)] hover:bg-cyan-500/30"
        aria-label="回報 Bug"
      >
        <Bug className="h-4 w-4" />
        <span className="text-xs">Bug 回報</span>
      </Button>
      <BugReportModal isOpen={open} onClose={() => setOpen(false)} />
    </>
  );
}

/** 組合：掛在 App 根層 */
export default function PublicBetaChrome() {
  return (
    <>
      <PublicBetaBadge />
      <PublicBetaWatermark />
      <PublicBetaBugFab />
    </>
  );
}
