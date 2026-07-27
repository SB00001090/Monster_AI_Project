/**
 * UI 樣式切換（50 款 + RGB / Hex）
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
import {
  applyThemeToDom,
  getThemeById,
  STORAGE_KEYS,
  UI_THEME_CATALOG,
  type UiThemeColors,
  type UiThemeDef,
} from "@/lib/themes/uiThemeCatalog";

interface UiThemeContextType {
  enabled: boolean;
  setEnabled: (v: boolean) => void;
  currentId: string;
  current: UiThemeDef;
  custom: Partial<UiThemeColors>;
  hiddenUnlocked: boolean;
  catalog: UiThemeDef[];
  visibleCatalog: UiThemeDef[];
  setThemeId: (id: string) => void;
  setCustomColor: (key: keyof UiThemeColors, hex: string) => void;
  resetCustom: () => void;
  unlockHidden: () => void;
}

const UiThemeContext = createContext<UiThemeContextType | undefined>(undefined);

function loadCustom(): Partial<UiThemeColors> {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.customRgb);
    return raw ? (JSON.parse(raw) as Partial<UiThemeColors>) : {};
  } catch {
    return {};
  }
}

export function UiThemeProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(true);
  const [currentId, setCurrentId] = useState(() => {
    if (typeof window === "undefined") return "cyber_pcb";
    return localStorage.getItem(STORAGE_KEYS.themeId) || "cyber_pcb";
  });
  const [custom, setCustom] = useState<Partial<UiThemeColors>>(loadCustom);
  const [hiddenUnlocked, setHiddenUnlocked] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(STORAGE_KEYS.hiddenUnlocked) === "true";
  });

  const current = useMemo(() => {
    const t = getThemeById(currentId);
    if (t && (!t.hidden || hiddenUnlocked)) return t;
    return getThemeById("cyber_pcb")!;
  }, [currentId, hiddenUnlocked]);

  const visibleCatalog = useMemo(
    () =>
      UI_THEME_CATALOG.filter((t) => !t.hidden || (hiddenUnlocked && t.id === "blue_rose_cage")),
    [hiddenUnlocked],
  );

  useEffect(() => {
    if (!enabled) return;
    applyThemeToDom(current.colors, custom);
  }, [current, custom, enabled]);

  const setThemeId = useCallback(
    (id: string) => {
      const t = getThemeById(id);
      if (!t) return;
      if (t.hidden && !hiddenUnlocked) return;
      setCurrentId(id);
      localStorage.setItem(STORAGE_KEYS.themeId, id);
    },
    [hiddenUnlocked],
  );

  const setCustomColor = useCallback((key: keyof UiThemeColors, hex: string) => {
    setCustom((prev) => {
      const next = { ...prev, [key]: hex };
      localStorage.setItem(STORAGE_KEYS.customRgb, JSON.stringify(next));
      return next;
    });
  }, []);

  const resetCustom = useCallback(() => {
    setCustom({});
    localStorage.removeItem(STORAGE_KEYS.customRgb);
  }, []);

  const unlockHidden = useCallback(() => {
    setHiddenUnlocked(true);
    localStorage.setItem(STORAGE_KEYS.hiddenUnlocked, "true");
  }, []);

  const value = useMemo(
    () => ({
      enabled,
      setEnabled,
      currentId: current.id,
      current,
      custom,
      hiddenUnlocked,
      catalog: UI_THEME_CATALOG,
      visibleCatalog,
      setThemeId,
      setCustomColor,
      resetCustom,
      unlockHidden,
    }),
    [
      enabled,
      current,
      custom,
      hiddenUnlocked,
      visibleCatalog,
      setThemeId,
      setCustomColor,
      resetCustom,
      unlockHidden,
    ],
  );

  return <UiThemeContext.Provider value={value}>{children}</UiThemeContext.Provider>;
}

export function useUiTheme() {
  const ctx = useContext(UiThemeContext);
  if (!ctx) throw new Error("useUiTheme must be used within UiThemeProvider");
  return ctx;
}
