/**
 * 啟動時檢查 GitHub Release 自動更新
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";

export interface UpdateInfo {
  updateAvailable: boolean;
  current: string;
  latest: string;
  url: string;
  body: string;
}

export function useAutoUpdate(enabled = true) {
  const [info, setInfo] = useState<UpdateInfo | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/accel/update/check");
        const data = await res.json();
        if (cancelled || !data?.ok) return;
        const next: UpdateInfo = {
          updateAvailable: !!data.update_available,
          current: data.current_version || "",
          latest: data.latest_version || "",
          url: data.html_url || "",
          body: data.body || "",
        };
        setInfo(next);
        if (next.updateAvailable && next.url) {
          toast.message(`有新版本 ${next.latest}`, {
            description: `目前 ${next.current} · 點擊開啟下載頁`,
            action: {
              label: "更新",
              onClick: () => window.open(next.url, "_blank", "noopener,noreferrer"),
            },
            duration: 12000,
          });
        }
      } catch {
        // 離線略過
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return info;
}
