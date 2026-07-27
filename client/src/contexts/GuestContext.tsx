/**
 * GuestContext — 訪客 / 公測額度核心
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 *
 * 公測訪客規則：
 * - 開啟 App 可直接訪客（無需登入）
 * - 每日 RP 對話上限 50 次
 * - 每日圖像生成上限 10 次
 * - 高階模組鎖定（完整 Guardian、本地 LLM 全功能、無水印等）
 * - 額度以 localStorage 按日重置
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

/**
 * 額度常數（當 unlimited_mode=true 時僅作顯示，不強制攔截）
 * 加速包預設：無限額
 */
export const BETA_DAILY_RP_LIMIT = 50;
export const BETA_DAILY_IMAGE_LIMIT = 10;
/** 全域無限額開關（對齊 config unlimited_mode） */
export const UNLIMITED_MODE =
  import.meta.env.VITE_UNLIMITED_MODE !== "false";

export const BETA_STORAGE_KEYS = {
  guestMode: "guest_mode",
  guestId: "guest_id",
  publicBeta: "monster_public_beta",
  day: "monster_beta_day",
  rpUsed: "monster_beta_rp_used",
  imageUsed: "monster_beta_image_used",
} as const;

/** 公測鎖定的高階模組（path 對應路由） */
export type LockedModuleId =
  | "guardian_full"
  | "local_llm_full"
  | "no_watermark"
  | "network_learning"
  | "toddler_learning"
  | "guardian_curriculum"
  | "deploy_cloud"
  | "commercial";

export interface LockedModule {
  id: LockedModuleId;
  path: string;
  titleZh: string;
  reasonZh: string;
}

export const BETA_LOCKED_MODULES: LockedModule[] = [
  {
    id: "guardian_full",
    path: "/guardian-sync",
    titleZh: "完整 Guardian",
    reasonZh: "公測訪客版鎖定完整守護同步；請升級正式版。",
  },
  {
    id: "local_llm_full",
    path: "/llm-settings",
    titleZh: "本地 LLM 全功能",
    reasonZh: "公測訪客僅提供基礎對話；完整本地模型設定需正式版。",
  },
  {
    id: "network_learning",
    path: "/network-learning",
    titleZh: "網路學習模組",
    reasonZh: "高階學習模組於公測訪客版鎖定。",
  },
  {
    id: "toddler_learning",
    path: "/toddler-learning",
    titleZh: "幼兒學習模組",
    reasonZh: "高階學習模組於公測訪客版鎖定。",
  },
  {
    id: "guardian_curriculum",
    path: "/guardian-curriculum",
    titleZh: "Guardian 課綱",
    reasonZh: "完整課綱進度於公測訪客版鎖定。",
  },
  {
    id: "deploy_cloud",
    path: "/deploy",
    titleZh: "雲端部署",
    reasonZh: "雲端部署僅正式版開放。",
  },
  {
    id: "commercial",
    path: "/pricing",
    titleZh: "商業 / 付費方案",
    reasonZh: "公測訪客免費；升級方案請至正式版或官網。",
  },
  {
    id: "no_watermark",
    path: "/settings",
    titleZh: "無水印輸出",
    reasonZh: "公測訪客版固定輕度水印，無法關閉。",
  },
];

export interface QuotaSnapshot {
  dayKey: string;
  rpUsed: number;
  imageUsed: number;
  rpRemaining: number;
  imageRemaining: number;
  rpLimit: number;
  imageLimit: number;
}

export interface ConsumeResult {
  ok: boolean;
  remaining: number;
  message?: string;
}

interface GuestContextType {
  isGuest: boolean;
  guestId: string;
  /** 公測訪客標記（本 APK 預設 true） */
  isPublicBeta: boolean;
  publisher: string;
  developer: string;
  badgeLabel: string;
  watermarkText: string;
  quota: QuotaSnapshot;
  setAsGuest: () => void;
  exitGuest: () => void;
  /** 嘗試消耗 1 次 RP；額度不足回傳 ok=false */
  consumeRp: () => ConsumeResult;
  /** 嘗試消耗 1 次圖像生成 */
  consumeImage: () => ConsumeResult;
  canRp: () => boolean;
  canImage: () => boolean;
  /** 路由是否為公測鎖定模組 */
  isPathLocked: (path: string) => boolean;
  getLockedModule: (path: string) => LockedModule | undefined;
  lockedModules: LockedModule[];
  refreshQuota: () => void;
}

const GuestContext = createContext<GuestContextType | undefined>(undefined);

function todayKey(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function readInt(key: string, fallback = 0): number {
  const raw = localStorage.getItem(key);
  if (raw == null) return fallback;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) ? n : fallback;
}

function ensureDayBucket(): { dayKey: string; rpUsed: number; imageUsed: number } {
  const day = todayKey();
  const stored = localStorage.getItem(BETA_STORAGE_KEYS.day);
  if (stored !== day) {
    localStorage.setItem(BETA_STORAGE_KEYS.day, day);
    localStorage.setItem(BETA_STORAGE_KEYS.rpUsed, "0");
    localStorage.setItem(BETA_STORAGE_KEYS.imageUsed, "0");
    return { dayKey: day, rpUsed: 0, imageUsed: 0 };
  }
  return {
    dayKey: day,
    rpUsed: Math.min(readInt(BETA_STORAGE_KEYS.rpUsed), BETA_DAILY_RP_LIMIT),
    imageUsed: Math.min(readInt(BETA_STORAGE_KEYS.imageUsed), BETA_DAILY_IMAGE_LIMIT),
  };
}

function buildQuota(): QuotaSnapshot {
  const { dayKey, rpUsed, imageUsed } = ensureDayBucket();
  return {
    dayKey,
    rpUsed,
    imageUsed,
    rpRemaining: Math.max(0, BETA_DAILY_RP_LIMIT - rpUsed),
    imageRemaining: Math.max(0, BETA_DAILY_IMAGE_LIMIT - imageUsed),
    rpLimit: BETA_DAILY_RP_LIMIT,
    imageLimit: BETA_DAILY_IMAGE_LIMIT,
  };
}

/** 是否應預設進入公測訪客（Capacitor / 本機 / Pages） */
export function shouldAutoEnterGuest(): boolean {
  if (typeof window === "undefined") return false;
  // 原生殼注入（MainActivity）
  const w = window as unknown as {
    Capacitor?: { isNativePlatform?: () => boolean };
    __MONSTER_FORCE_GUEST__?: boolean;
    __MONSTER_PUBLIC_BETA__?: boolean;
  };
  if (w.__MONSTER_FORCE_GUEST__ || w.__MONSTER_PUBLIC_BETA__) return true;
  // Capacitor 原生殼
  if (w.Capacitor?.isNativePlatform?.()) return true;
  // 建置旗標
  if (import.meta.env.VITE_PUBLIC_BETA === "true") return true;
  if (import.meta.env.VITE_FORCE_GUEST === "true") return true;
  const host = window.location.hostname;
  return (
    host.includes("pages.dev") ||
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "monster-ai-hk.pages.dev"
  );
}

export function GuestProvider({ children }: { children: ReactNode }) {
  const [isGuest, setIsGuest] = useState(false);
  const [guestId, setGuestId] = useState("");
  const [quota, setQuota] = useState<QuotaSnapshot>(() => {
    if (typeof window === "undefined") {
      return {
        dayKey: "",
        rpUsed: 0,
        imageUsed: 0,
        rpRemaining: BETA_DAILY_RP_LIMIT,
        imageRemaining: BETA_DAILY_IMAGE_LIMIT,
        rpLimit: BETA_DAILY_RP_LIMIT,
        imageLimit: BETA_DAILY_IMAGE_LIMIT,
      };
    }
    return buildQuota();
  });

  const isPublicBeta = true; // 本 APK / 公測殼固定為公測
  const publisher = "Monster_Ai_hk";
  const developer = "suckbob";
  const badgeLabel = "公測版 · 訪客免費";
  const watermarkText = "公測訪客｜Monster_Ai_hk";

  const refreshQuota = useCallback(() => {
    setQuota(buildQuota());
  }, []);

  // 初始化：讀取訪客 + 公測標記 + 額度
  useEffect(() => {
    const storedGuestMode = localStorage.getItem(BETA_STORAGE_KEYS.guestMode);
    const storedGuestId = localStorage.getItem(BETA_STORAGE_KEYS.guestId);

    localStorage.setItem(BETA_STORAGE_KEYS.publicBeta, "true");

    if (storedGuestMode === "true" && storedGuestId) {
      setIsGuest(true);
      setGuestId(storedGuestId);
    } else if (shouldAutoEnterGuest()) {
      // 公測 APK：首次開啟直接訪客
      const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
      localStorage.setItem(BETA_STORAGE_KEYS.guestMode, "true");
      localStorage.setItem(BETA_STORAGE_KEYS.guestId, newGuestId);
      setIsGuest(true);
      setGuestId(newGuestId);
    }

    setQuota(buildQuota());
  }, []);

  // 跨日時（長駐 App）每分鐘檢查一次 day key
  useEffect(() => {
    const id = window.setInterval(() => {
      const day = todayKey();
      if (localStorage.getItem(BETA_STORAGE_KEYS.day) !== day) {
        setQuota(buildQuota());
      }
    }, 60_000);
    return () => window.clearInterval(id);
  }, []);

  const setAsGuest = useCallback(() => {
    const newGuestId = `guest_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    localStorage.setItem(BETA_STORAGE_KEYS.guestMode, "true");
    localStorage.setItem(BETA_STORAGE_KEYS.guestId, newGuestId);
    localStorage.setItem(BETA_STORAGE_KEYS.publicBeta, "true");
    setIsGuest(true);
    setGuestId(newGuestId);
    setQuota(buildQuota());
  }, []);

  const exitGuest = useCallback(() => {
    // 公測殼仍可退出訪客以便測試登入流；額度資料保留
    localStorage.removeItem(BETA_STORAGE_KEYS.guestMode);
    localStorage.removeItem(BETA_STORAGE_KEYS.guestId);
    setIsGuest(false);
    setGuestId("");
  }, []);

  const consumeRp = useCallback((): ConsumeResult => {
    // 無限額：永遠允許
    if (UNLIMITED_MODE) {
      return { ok: true, remaining: 999999 };
    }
    const q = buildQuota();
    if (q.rpRemaining <= 0) {
      setQuota(q);
      return {
        ok: false,
        remaining: 0,
        message: `今日 RP 對話額度已用完（${BETA_DAILY_RP_LIMIT} 次）。請明日再試或升級正式版。`,
      };
    }
    const next = q.rpUsed + 1;
    localStorage.setItem(BETA_STORAGE_KEYS.rpUsed, String(next));
    const updated = buildQuota();
    setQuota(updated);
    return { ok: true, remaining: updated.rpRemaining };
  }, []);

  const consumeImage = useCallback((): ConsumeResult => {
    if (UNLIMITED_MODE) {
      return { ok: true, remaining: 999999 };
    }
    const q = buildQuota();
    if (q.imageRemaining <= 0) {
      setQuota(q);
      return {
        ok: false,
        remaining: 0,
        message: `今日圖像生成額度已用完（${BETA_DAILY_IMAGE_LIMIT} 次）。請明日再試或升級正式版。`,
      };
    }
    const next = q.imageUsed + 1;
    localStorage.setItem(BETA_STORAGE_KEYS.imageUsed, String(next));
    const updated = buildQuota();
    setQuota(updated);
    return { ok: true, remaining: updated.imageRemaining };
  }, []);

  const canRp = useCallback(() => UNLIMITED_MODE || buildQuota().rpRemaining > 0, []);
  const canImage = useCallback(() => UNLIMITED_MODE || buildQuota().imageRemaining > 0, []);

  const isPathLocked = useCallback(
    (path: string) => {
      if (!isGuest && !isPublicBeta) return false;
      // 訪客公測：鎖定高階 path
      return BETA_LOCKED_MODULES.some(
        (m) => path === m.path || path.startsWith(`${m.path}/`),
      );
    },
    [isGuest, isPublicBeta],
  );

  const getLockedModule = useCallback(
    (path: string) =>
      BETA_LOCKED_MODULES.find(
        (m) => path === m.path || path.startsWith(`${m.path}/`),
      ),
    [],
  );

  const value = useMemo<GuestContextType>(
    () => ({
      isGuest,
      guestId,
      isPublicBeta,
      publisher,
      developer,
      badgeLabel,
      watermarkText,
      quota,
      setAsGuest,
      exitGuest,
      consumeRp,
      consumeImage,
      canRp,
      canImage,
      isPathLocked,
      getLockedModule,
      lockedModules: BETA_LOCKED_MODULES,
      refreshQuota,
    }),
    [
      isGuest,
      guestId,
      quota,
      setAsGuest,
      exitGuest,
      consumeRp,
      consumeImage,
      canRp,
      canImage,
      isPathLocked,
      getLockedModule,
      refreshQuota,
    ],
  );

  return <GuestContext.Provider value={value}>{children}</GuestContext.Provider>;
}

export function useGuest() {
  const context = useContext(GuestContext);
  if (!context) {
    throw new Error("useGuest must be used within GuestProvider");
  }
  return context;
}
