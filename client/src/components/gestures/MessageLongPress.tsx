/**
 * 長按訊息 → 操作選單（複製 / 重新生成 / 回報）
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";

interface Props {
  text: string;
  children: ReactNode;
  onRegenerate?: () => void;
  onReport?: () => void;
}

export default function MessageLongPress({
  text,
  children,
  onRegenerate,
  onReport,
}: Props) {
  const timer = useRef<number | null>(null);
  const [menu, setMenu] = useState(false);

  const clear = () => {
    if (timer.current) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  };

  const start = () => {
    clear();
    timer.current = window.setTimeout(() => setMenu(true), 480);
  };

  return (
    <div
      className="relative"
      data-monster-msg="1"
      onTouchStart={start}
      onTouchEnd={clear}
      onTouchMove={clear}
      onContextMenu={(e) => {
        e.preventDefault();
        setMenu(true);
      }}
    >
      {children}
      {menu && (
        <div className="absolute z-30 mt-1 flex flex-wrap gap-1 rounded-lg border border-border bg-card p-1 shadow-lg">
          <button
            type="button"
            className="rounded px-2 py-1 text-xs hover:bg-accent"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(text);
                toast.success("已複製");
              } catch {
                toast.error("複製失敗");
              }
              setMenu(false);
            }}
          >
            複製
          </button>
          <button
            type="button"
            className="rounded px-2 py-1 text-xs hover:bg-accent"
            onClick={() => {
              onRegenerate?.();
              window.dispatchEvent(new CustomEvent("monster:gesture-continue"));
              setMenu(false);
            }}
          >
            重新生成
          </button>
          <button
            type="button"
            className="rounded px-2 py-1 text-xs hover:bg-accent"
            onClick={() => {
              onReport?.();
              window.dispatchEvent(new CustomEvent("monster:emergency-feedback"));
              setMenu(false);
            }}
          >
            回報
          </button>
          <button
            type="button"
            className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
            onClick={() => setMenu(false)}
          >
            關閉
          </button>
        </div>
      )}
    </div>
  );
}
