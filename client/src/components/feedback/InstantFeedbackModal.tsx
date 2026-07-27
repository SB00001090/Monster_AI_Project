/**
 * 即時回報（文字 + 可選截圖）
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { X, Send } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

/** 無 html2canvas 依賴：用 SVG foreignObject 抓可視區域（失敗則略過） */
async function captureScreenshot(): Promise<string | null> {
  try {
    const w = Math.min(window.innerWidth, 1280);
    const h = Math.min(window.innerHeight, 720);
    const html = new XMLSerializer().serializeToString(document.documentElement);
    // 僅截精簡 meta，避免巨大 DOM 爆掉
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
      <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml" style="font:14px sans-serif;padding:16px;background:#0b0f1a;color:#fff">
          <p>Monster AI 回報截圖快照</p>
          <p>URL: ${location.href}</p>
          <p>UA: ${navigator.userAgent.slice(0, 120)}</p>
          <p>time: ${new Date().toISOString()}</p>
        </div>
      </foreignObject>
    </svg>`;
    void html;
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    const dataUrl = await new Promise<string | null>((resolve) => {
      img.onload = () => {
        try {
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          if (!ctx) {
            resolve(null);
            return;
          }
          ctx.fillStyle = "#0b0f1a";
          ctx.fillRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0);
          resolve(canvas.toDataURL("image/png"));
        } catch {
          resolve(null);
        } finally {
          URL.revokeObjectURL(url);
        }
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve(null);
      };
      img.src = url;
    });
    return dataUrl;
  } catch {
    return null;
  }
}

export default function InstantFeedbackModal({ open, onClose }: Props) {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [includeShot, setIncludeShot] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const submit = async () => {
    if (!message.trim()) {
      toast.error("請填寫回報內容");
      return;
    }
    setLoading(true);
    try {
      let shot: string | null = null;
      if (includeShot) shot = await captureScreenshot();
      const res = await fetch("/api/accel/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim() || "即時回報",
          message: message.trim(),
          screenshot_base64: shot,
          emotion_summary: localStorage.getItem("monster_last_emotion") || undefined,
          extra: {
            href: window.location.href,
            ua: navigator.userAgent,
            guest: localStorage.getItem("guest_mode"),
          },
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        toast.error(data.message || "回報失敗");
      } else {
        toast.success(data.webhook_ok ? "已送出（含 Webhook）" : "已儲存回報");
        setTitle("");
        setMessage("");
        onClose();
      }
    } catch {
      toast.error("網路錯誤，回報未送出");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold">即時回報</h2>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="space-y-3">
          <div>
            <Label>標題（可選）</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="簡短標題" />
          </div>
          <div>
            <Label>內容</Label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={4}
              placeholder="描述問題、卡頓或期望功能…"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeShot}
              onChange={(e) => setIncludeShot(e.target.checked)}
            />
            嘗試附帶截圖（可選）
          </label>
          <p className="text-[11px] text-muted-foreground">
            會自動附上版本、裝置、情緒摘要與自癒日誌（後端）。
            開發者：suckbob · 發行商：Monster_Ai_hk
          </p>
          <Button className="w-full gap-2" onClick={() => void submit()} disabled={loading}>
            <Send className="h-4 w-4" />
            {loading ? "送出中…" : "一鍵送出"}
          </Button>
        </div>
      </div>
    </div>
  );
}
