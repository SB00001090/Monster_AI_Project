/**
 * 公測鎖定模組升級提示
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { LockedModule } from "@/contexts/GuestContext";

const OFFICIAL_URL =
  import.meta.env.VITE_OFFICIAL_DOWNLOAD_URL || "https://monster-ai-hk.pages.dev";

interface Props {
  open: boolean;
  module: LockedModule | null;
  onClose: () => void;
}

export default function BetaUpgradePrompt({ open, module, onClose }: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="border-pink-500/40 bg-card text-card-foreground sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-pink-300">功能鎖定 · 公測訪客</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {module?.titleZh ?? "高階模組"} 在訪客公測版不可用。
          </DialogDescription>
        </DialogHeader>
        <p className="text-sm leading-relaxed text-foreground/90">
          {module?.reasonZh ?? "請升級正式版解鎖完整功能（無水印、完整 Guardian、本地 LLM 等）。"}
        </p>
        <p className="text-xs text-muted-foreground">
          發行商：Monster_Ai_hk · 開發者：suckbob
        </p>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={onClose}>
            返回
          </Button>
          <Button
            onClick={() => {
              window.open(OFFICIAL_URL, "_blank", "noopener,noreferrer");
            }}
          >
            了解正式版
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
