/**
 * 手勢操作系統
 * 開發者：suckbob | 發行商：Monster_Ai_hk
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
import { STORAGE_KEYS } from "@/lib/themes/uiThemeCatalog";

export type GestureSensitivity = "low" | "medium" | "high";

export type GestureAction =
  | "continue_generate"
  | "undo"
  | "message_menu"
  | "open_settings"
  | "open_history"
  | "font_zoom"
  | "emergency_feedback";

export interface GestureConfig {
  enabled: boolean;
  sensitivity: GestureSensitivity;
  leftHanded: boolean;
  /** 輸入框聚焦時暫停易衝突手勢 */
  pauseOnInputFocus: boolean;
}

interface GestureContextType extends GestureConfig {
  setEnabled: (v: boolean) => void;
  setSensitivity: (s: GestureSensitivity) => void;
  setLeftHanded: (v: boolean) => void;
  setPauseOnInputFocus: (v: boolean) => void;
  inputFocused: boolean;
  setInputFocused: (v: boolean) => void;
  /** 註冊動作處理 */
  handlers: Partial<Record<GestureAction, () => void>>;
  registerHandler: (action: GestureAction, fn: (() => void) | null) => void;
  fontScale: number;
  setFontScale: (n: number) => void;
  thresholdPx: number;
}

const defaults: GestureConfig = {
  enabled: true,
  sensitivity: "medium",
  leftHanded: false,
  pauseOnInputFocus: true,
};

const GestureContext = createContext<GestureContextType | undefined>(undefined);

function loadCfg(): GestureConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.gestures);
    if (!raw) return defaults;
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return defaults;
  }
}

export function GestureProvider({ children }: { children: ReactNode }) {
  const [cfg, setCfg] = useState<GestureConfig>(loadCfg);
  const [inputFocused, setInputFocused] = useState(false);
  const [handlers, setHandlers] = useState<Partial<Record<GestureAction, () => void>>>({});
  const [fontScale, setFontScale] = useState(1);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.gestures, JSON.stringify(cfg));
  }, [cfg]);

  useEffect(() => {
    document.documentElement.style.setProperty("--monster-font-scale", String(fontScale));
  }, [fontScale]);

  const registerHandler = useCallback((action: GestureAction, fn: (() => void) | null) => {
    setHandlers((prev) => {
      const next = { ...prev };
      if (fn) next[action] = fn;
      else delete next[action];
      return next;
    });
  }, []);

  const thresholdPx = useMemo(() => {
    if (cfg.sensitivity === "high") return 36;
    if (cfg.sensitivity === "low") return 80;
    return 56;
  }, [cfg.sensitivity]);

  const value = useMemo<GestureContextType>(
    () => ({
      ...cfg,
      setEnabled: (v) => setCfg((c) => ({ ...c, enabled: v })),
      setSensitivity: (s) => setCfg((c) => ({ ...c, sensitivity: s })),
      setLeftHanded: (v) => setCfg((c) => ({ ...c, leftHanded: v })),
      setPauseOnInputFocus: (v) => setCfg((c) => ({ ...c, pauseOnInputFocus: v })),
      inputFocused,
      setInputFocused,
      handlers,
      registerHandler,
      fontScale,
      setFontScale,
      thresholdPx,
    }),
    [cfg, inputFocused, handlers, registerHandler, fontScale, thresholdPx],
  );

  return <GestureContext.Provider value={value}>{children}</GestureContext.Provider>;
}

export function useGestures() {
  const ctx = useContext(GestureContext);
  if (!ctx) throw new Error("useGestures must be used within GestureProvider");
  return ctx;
}
