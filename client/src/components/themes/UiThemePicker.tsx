/**
 * 設定 → 介面 → 選擇款式
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useState } from "react";
import { useUiTheme } from "@/contexts/UiThemeContext";
import type { UiThemeColors } from "@/lib/themes/uiThemeCatalog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

const COLOR_FIELDS: { key: keyof UiThemeColors; label: string }[] = [
  { key: "primary", label: "主色" },
  { key: "secondary", label: "輔色" },
  { key: "accent", label: "強調色" },
  { key: "background", label: "背景" },
  { key: "foreground", label: "文字" },
];

export default function UiThemePicker() {
  const {
    enabled,
    setEnabled,
    currentId,
    current,
    custom,
    visibleCatalog,
    setThemeId,
    setCustomColor,
    resetCustom,
  } = useUiTheme();
  const [hexDraft, setHexDraft] = useState<Record<string, string>>({});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">介面樣式</h3>
          <p className="text-sm text-muted-foreground">
            共 {visibleCatalog.length} 款（可擴至 50）· 支援 RGB / Hex
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="theme-en">啟用樣式系統</Label>
          <Switch id="theme-en" checked={enabled} onCheckedChange={setEnabled} />
        </div>
      </div>

      {/* 即時預覽 */}
      <div
        className="rounded-xl border p-4"
        style={{
          background: custom.background || current.colors.background,
          color: custom.foreground || current.colors.foreground,
          borderColor: custom.border || current.colors.border,
        }}
      >
        <p className="text-xs opacity-70 mb-2">即時預覽 · {current.nameZh}</p>
        <div className="flex flex-wrap gap-2">
          {COLOR_FIELDS.map(({ key, label }) => {
            const c = custom[key] || current.colors[key];
            return (
              <div key={key} className="flex items-center gap-1.5 text-xs">
                <span
                  className="inline-block h-5 w-5 rounded-full border"
                  style={{ background: c, borderColor: "#fff3" }}
                />
                {label}
              </div>
            );
          })}
        </div>
      </div>

      {/* 主題列表 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-72 overflow-y-auto pr-1">
        {visibleCatalog.map((t) => {
          const active = t.id === currentId;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setThemeId(t.id)}
              className={`rounded-lg border p-2 text-left transition ${
                active ? "outline outline-2 outline-offset-1" : "opacity-90 hover:opacity-100"
              }`}
              style={{
                borderColor: t.colors.border,
                background: t.colors.card,
                color: t.colors.foreground,
                outlineColor: active ? t.colors.primary : undefined,
              }}
            >
              <div className="flex gap-1 mb-1">
                {[t.colors.primary, t.colors.accent, t.colors.secondary].map((c) => (
                  <span
                    key={c}
                    className="h-3 w-3 rounded-full"
                    style={{ background: c }}
                  />
                ))}
              </div>
              <div className="text-xs font-medium truncate">{t.nameZh}</div>
              {t.hidden && (
                <Badge variant="outline" className="mt-1 text-[10px] border-blue-400 text-blue-300">
                  Developer Hidden
                </Badge>
              )}
            </button>
          );
        })}
      </div>

      {/* Hex / RGB 調整 */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="font-medium">自訂色號</h4>
          <Button type="button" size="sm" variant="outline" onClick={resetCustom}>
            重設
          </Button>
        </div>
        {COLOR_FIELDS.map(({ key, label }) => {
          const value = custom[key] || current.colors[key];
          return (
            <div key={key} className="grid grid-cols-[80px_1fr_48px] items-center gap-2">
              <Label>{label}</Label>
              <Input
                value={hexDraft[key] ?? value}
                onChange={(e) => setHexDraft((d) => ({ ...d, [key]: e.target.value }))}
                onBlur={() => {
                  const v = (hexDraft[key] ?? value).trim();
                  if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(v)) {
                    setCustomColor(key, v);
                  }
                }}
                placeholder="#00E5FF"
              />
              <input
                type="color"
                className="h-9 w-12 cursor-pointer rounded border-0 bg-transparent"
                value={/^#([0-9a-fA-F]{6})$/.test(value) ? value : "#000000"}
                onChange={(e) => setCustomColor(key, e.target.value)}
                aria-label={label}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
