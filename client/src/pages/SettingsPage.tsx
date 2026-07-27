import { useRef, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { useAuth } from "@/_core/hooks/useAuth";
import { useTheme } from "@/contexts/ThemeContext";
import { useGuest } from "@/contexts/GuestContext";
import { useGestures, type GestureSensitivity } from "@/contexts/GestureContext";
import { useUiTheme } from "@/contexts/UiThemeContext";
import OAuthProviderButtons from "@/components/OAuthProviderButtons";
import GuardianAccountPanel from "@/components/GuardianAccountPanel";
import UiThemePicker from "@/components/themes/UiThemePicker";
import InstantFeedbackModal from "@/components/feedback/InstantFeedbackModal";
import LLMSettings from "./LLMSettings";
import { useLocation } from "wouter";

type SettingsTab =
  | "profile"
  | "interface"
  | "gestures"
  | "theme"
  | "llm"
  | "safety"
  | "account"
  | "about";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { isGuest } = useGuest();

  const tabs = [
    { id: "profile" as const, label: "個人資料", icon: "👤" },
    { id: "interface" as const, label: "介面", icon: "🖼️" },
    { id: "gestures" as const, label: "手勢操作", icon: "👆" },
    { id: "theme" as const, label: "明暗主題", icon: "🎨" },
    { id: "llm" as const, label: "LLM 模型", icon: "🤖" },
    { id: "safety" as const, label: "安全設定", icon: "🛡️" },
    { id: "account" as const, label: "帳號管理", icon: "⚙️" },
    { id: "about" as const, label: "關於", icon: "ℹ️" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">設定</h2>
        <p className="text-muted-foreground mt-1">
          管理偏好 · 無限額 · 無審查 RP · 自癒預設開啟
        </p>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-border pb-3">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={activeTab === tab.id ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab(tab.id)}
            className="gap-2"
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </Button>
        ))}
      </div>

      {activeTab === "profile" && <ProfileSection user={user} isGuest={isGuest} />}
      {activeTab === "interface" && (
        <Card>
          <CardHeader>
            <CardTitle>介面樣式</CardTitle>
            <CardDescription>設定 → 介面 → 選擇款式（50 款架構）</CardDescription>
          </CardHeader>
          <CardContent>
            <UiThemePicker />
          </CardContent>
        </Card>
      )}
      {activeTab === "gestures" && <GesturesSection />}
      {activeTab === "theme" && <ThemeSection theme={theme} toggleTheme={toggleTheme} />}
      {activeTab === "llm" && <LLMSettings />}
      {activeTab === "safety" && <SafetySection />}
      {activeTab === "account" && <AccountSection user={user} isGuest={isGuest} />}
      {activeTab === "about" && <AboutSection />}
    </div>
  );
}

function GesturesSection() {
  const {
    enabled,
    setEnabled,
    sensitivity,
    setSensitivity,
    leftHanded,
    setLeftHanded,
    pauseOnInputFocus,
    setPauseOnInputFocus,
  } = useGestures();
  const levels: GestureSensitivity[] = ["low", "medium", "high"];
  const labels: Record<GestureSensitivity, string> = {
    low: "低",
    medium: "中",
    high: "高",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>手勢操作</CardTitle>
        <CardDescription>設定 → 手勢操作 · 可獨立開關</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label>啟用手勢系統</Label>
          <Switch checked={enabled} onCheckedChange={setEnabled} />
        </div>
        <div className="flex items-center justify-between">
          <Label>輸入框聚焦時暫停衝突手勢</Label>
          <Switch checked={pauseOnInputFocus} onCheckedChange={setPauseOnInputFocus} />
        </div>
        <div className="flex items-center justify-between">
          <Label>慣用左手（鏡像左右滑）</Label>
          <Switch checked={leftHanded} onCheckedChange={setLeftHanded} />
        </div>
        <div>
          <Label className="mb-2 block">敏感度</Label>
          <div className="flex gap-2">
            {levels.map((l) => (
              <Button
                key={l}
                size="sm"
                variant={sensitivity === l ? "default" : "outline"}
                onClick={() => setSensitivity(l)}
              >
                {labels[l]}
              </Button>
            ))}
          </div>
        </div>
        <ul className="text-sm text-muted-foreground space-y-1 list-disc pl-5">
          <li>單指右滑 → 繼續生成</li>
          <li>單指左滑 → 撤回</li>
          <li>長按訊息 → 操作選單（複製/重新生成/回報）</li>
          <li>邊緣右滑 → 開啟設定</li>
          <li>邊緣左滑 → 開啟歷史</li>
          <li>雙指縮放 → 調整字體</li>
          <li>三指點擊 → 緊急回報</li>
        </ul>
      </CardContent>
    </Card>
  );
}

function AboutSection() {
  const clickRef = useRef(0);
  const timerRef = useRef<number | null>(null);
  const { hiddenUnlocked, current } = useUiTheme();
  const [fbOpen, setFbOpen] = useState(false);
  const version = "1.0.0-accel";

  const onVersionClick = () => {
    clickRef.current += 1;
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      clickRef.current = 0;
    }, 2000);
    if (clickRef.current >= 7) {
      clickRef.current = 0;
      if (hiddenUnlocked) {
        toast.message("藍玫瑰和籠子 已解鎖");
        return;
      }
      window.dispatchEvent(new CustomEvent("monster:unlock-blue-rose"));
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>關於 Monster AI</CardTitle>
        <CardDescription>發行商 Monster_Ai_hk · 開發者 suckbob</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <button
          type="button"
          onClick={onVersionClick}
          className="text-left rounded-lg border border-border px-3 py-2 hover:bg-accent/40 transition w-full"
        >
          <div className="text-sm text-muted-foreground">版本號（連點 7 次…）</div>
          <div className="font-mono text-lg">{version}</div>
        </button>
        <div className="text-sm space-y-1">
          <p>目前介面樣式：{current.nameZh}</p>
          <p>
            隱藏主題：
            {hiddenUnlocked ? (
              <Badge className="ml-2">藍玫瑰和籠子 已解鎖</Badge>
            ) : (
              <span className="text-muted-foreground"> 未解鎖</span>
            )}
          </p>
          <p className="text-muted-foreground text-xs">
            這是開發者私人收藏的隱藏主題，靈感來自某位聲音獨特的歌手。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => setFbOpen(true)}>即時回報</Button>
          <Button
            variant="outline"
            onClick={async () => {
              try {
                const r = await fetch("/api/accel/update/check");
                const d = await r.json();
                if (d.update_available) {
                  toast.message(`新版本 ${d.latest_version}`, {
                    action: {
                      label: "下載",
                      onClick: () => window.open(d.html_url, "_blank"),
                    },
                  });
                } else {
                  toast.success("已是最新或尚無 Release");
                }
              } catch {
                toast.error("檢查更新失敗");
              }
            }}
          >
            檢查更新
          </Button>
        </div>
        <InstantFeedbackModal open={fbOpen} onClose={() => setFbOpen(false)} />
      </CardContent>
    </Card>
  );
}

function ProfileSection({ user, isGuest }: { user: any; isGuest: boolean }) {
  const [displayName, setDisplayName] = useState(user?.name || "");

  return (
    <Card>
      <CardHeader>
        <CardTitle>個人資料</CardTitle>
        <CardDescription>管理您的顯示名稱和個人資訊</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-2xl">
            {isGuest ? "👻" : user?.name?.[0]?.toUpperCase() || "U"}
          </div>
          <div>
            <p className="font-medium">{isGuest ? "臨時訪客" : user?.name || "用戶"}</p>
            <Badge variant={isGuest ? "secondary" : "default"}>
              {isGuest ? "臨時帳號" : "正式帳號"}
            </Badge>
          </div>
        </div>

        <div className="space-y-2">
          <Label>顯示名稱</Label>
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="輸入您的顯示名稱"
            disabled={isGuest}
          />
          {isGuest && (
            <p className="text-xs text-muted-foreground">臨時帳號無法修改個人資料，請登入正式帳號</p>
          )}
        </div>

        {!isGuest && (
          <Button
            onClick={() => toast.success("個人資料已更新")}
            disabled={!displayName.trim()}
          >
            保存變更
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function ThemeSection({ theme, toggleTheme }: { theme: string; toggleTheme?: () => void }) {
  const themes = [
    { id: "dark", label: "深色模式", icon: "🌙", description: "護眼深色主題" },
    { id: "light", label: "淺色模式", icon: "☀️", description: "明亮淺色主題" },
    { id: "system", label: "跟隨系統", icon: "💻", description: "自動跟隨系統設定" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>主題外觀</CardTitle>
        <CardDescription>選擇您喜歡的介面主題</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {themes.map((t) => (
            <div
              key={t.id}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                theme === t.id
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => {
                if (toggleTheme) toggleTheme();
                toast.success(`主題已切換`);
              }}
            >
              <div className="text-center">
                <div className="text-3xl mb-2">{t.icon}</div>
                <div className="font-medium">{t.label}</div>
                <div className="text-xs text-muted-foreground mt-1">{t.description}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SafetySection() {
  // 加速包：預設無審查成人 RP；僅保留未成年硬規則
  const [contentFilter, setContentFilter] = useState("uncensored");

  const filterLevels = [
    {
      id: "uncensored",
      label: "無審查（預設）",
      description: "本地虛構成人 RP / 圖像最大化創意，不自我審查",
      icon: "🔓",
    },
    { id: "minimal", label: "最低", description: "僅封鎖涉及未成年人的內容", icon: "🛡️" },
    { id: "moderate", label: "適中", description: "額外過濾部分敏感標籤", icon: "⚠️" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>安全設定</CardTitle>
        <CardDescription>uncensored=true · 無限額 · 自癒開啟</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          {filterLevels.map((level) => (
            <div
              key={level.id}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                contentFilter === level.id
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => {
                setContentFilter(level.id);
                localStorage.setItem("monster_content_filter", level.id);
                toast.success(`內容模式：${level.label}`);
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{level.icon}</span>
                <div>
                  <div className="font-medium">{level.label}</div>
                  <div className="text-xs text-muted-foreground">{level.description}</div>
                </div>
                {contentFilter === level.id && (
                  <Badge className="ml-auto">目前</Badge>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
          <p className="text-sm text-destructive font-medium">⚠️ 不可更改的硬規則</p>
          <p className="text-xs text-muted-foreground mt-1">
            禁止未成年人性內容與真實犯罪可執行協助。此規則不可繞過。
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function AccountSection({ user, isGuest }: { user: any; isGuest: boolean }) {
  const [, setLocation] = useLocation();

  return (
    <Card>
      <CardHeader>
        <CardTitle>帳號管理</CardTitle>
        <CardDescription>管理您的帳號狀態和數據</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isGuest ? (
          <div className="space-y-4">
            <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <p className="font-medium text-amber-600">👻 您目前使用臨時帳號</p>
              <p className="text-sm text-muted-foreground mt-1">
                臨時帳號的數據可能在一段時間後被清除。建議登入正式帳號以保留所有數據。
              </p>
            </div>
            <div className="space-y-2">
              <h4 className="font-medium">臨時帳號限制：</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 聊天記錄可能在 7 天後過期</li>
                <li>• 無法分享角色到社群</li>
                <li>• 無法使用進階 AI Agent 功能</li>
                <li>• 存儲空間有限</li>
              </ul>
            </div>
            <OAuthProviderButtons size="default" />
            <Button className="w-full" variant="outline" onClick={() => setLocation("/login")}>
              前往登入頁
            </Button>
            <GuardianAccountPanel />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
              <p className="font-medium text-green-600">✅ 正式帳號</p>
              <p className="text-sm text-muted-foreground mt-1">
                您的所有數據都已安全保存。享受完整功能。
              </p>
            </div>

            <Button
              className="w-full"
              variant="secondary"
              onClick={() => setLocation("/guardian-sync")}
            >
              🛡️ Guardian Ai 雲端同步
            </Button>

            <GuardianAccountPanel />

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg border">
                <p className="text-xs text-muted-foreground">帳號 ID</p>
                <p className="font-mono text-sm">{user?.id || "N/A"}</p>
              </div>
              <div className="p-3 rounded-lg border">
                <p className="text-xs text-muted-foreground">角色</p>
                <p className="text-sm">{user?.role === "admin" ? "管理員" : "用戶"}</p>
              </div>
              <div className="p-3 rounded-lg border">
                <p className="text-xs text-muted-foreground">註冊時間</p>
                <p className="text-sm">{user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : "N/A"}</p>
              </div>
              <div className="p-3 rounded-lg border">
                <p className="text-xs text-muted-foreground">帳號狀態</p>
                <Badge variant="default">活躍</Badge>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
