/**
 * 50 款 UI 介面樣式目錄（可擴展）
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
export interface UiThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  foreground: string;
  card: string;
  border: string;
  muted: string;
}

export interface UiThemeDef {
  id: string;
  nameZh: string;
  nameEn: string;
  category: string;
  hidden?: boolean;
  description?: string;
  colors: UiThemeColors;
}

const core: UiThemeDef[] = [
  {
    id: "cyber_pcb",
    nameZh: "賽博風（PCB）",
    nameEn: "Cyber PCB",
    category: "cyber",
    colors: {
      primary: "#00FF9C",
      secondary: "#0A3D2E",
      accent: "#FFB800",
      background: "#06140F",
      foreground: "#E8FFF4",
      card: "#0C1F18",
      border: "#1A5C44",
      muted: "#7AAE96",
    },
  },
  {
    id: "gothic",
    nameZh: "哥德風",
    nameEn: "Gothic",
    category: "gothic",
    colors: {
      primary: "#C9A0FF",
      secondary: "#2A1838",
      accent: "#9B1DFF",
      background: "#0D0A12",
      foreground: "#F0E6FF",
      card: "#16101F",
      border: "#3D2A55",
      muted: "#A08CB8",
    },
  },
  {
    id: "japanese",
    nameZh: "日式（和風）",
    nameEn: "Japanese",
    category: "japanese",
    colors: {
      primary: "#E85D4C",
      secondary: "#F5E6D3",
      accent: "#2C5F2D",
      background: "#1A1410",
      foreground: "#FFF8F0",
      card: "#261E18",
      border: "#5C4033",
      muted: "#C4A484",
    },
  },
  {
    id: "hk_neon",
    nameZh: "港式霓虹",
    nameEn: "HK Neon",
    category: "neon",
    colors: {
      primary: "#FF2E63",
      secondary: "#08D9D6",
      accent: "#FFD700",
      background: "#0B0B14",
      foreground: "#FFFFFF",
      card: "#151525",
      border: "#FF2E6388",
      muted: "#9AA0C0",
    },
  },
  {
    id: "minimal_dark",
    nameZh: "極簡黑",
    nameEn: "Minimal Dark",
    category: "minimal",
    colors: {
      primary: "#FFFFFF",
      secondary: "#333333",
      accent: "#888888",
      background: "#0A0A0A",
      foreground: "#F5F5F5",
      card: "#141414",
      border: "#2A2A2A",
      muted: "#888888",
    },
  },
  {
    id: "minimal_light",
    nameZh: "極簡白",
    nameEn: "Minimal Light",
    category: "minimal",
    colors: {
      primary: "#111111",
      secondary: "#EEEEEE",
      accent: "#555555",
      background: "#FAFAFA",
      foreground: "#111111",
      card: "#FFFFFF",
      border: "#E5E5E5",
      muted: "#777777",
    },
  },
  {
    id: "neon_cyber",
    nameZh: "霓虹賽博",
    nameEn: "Neon Cyber",
    category: "cyber",
    colors: {
      primary: "#00E5FF",
      secondary: "#FF4D9A",
      accent: "#9B6DFF",
      background: "#0B0F1A",
      foreground: "#F2F5FF",
      card: "#151B2E",
      border: "#2A3A6A",
      muted: "#9AA3B8",
    },
  },
  {
    id: "blood_gothic",
    nameZh: "血色哥德",
    nameEn: "Blood Gothic",
    category: "gothic",
    colors: {
      primary: "#FF1A3C",
      secondary: "#3A0A12",
      accent: "#8B0000",
      background: "#0A0506",
      foreground: "#FFE8EC",
      card: "#16080C",
      border: "#5C1018",
      muted: "#B08088",
    },
  },
  {
    id: "modern_japanese",
    nameZh: "現代日系",
    nameEn: "Modern Japanese",
    category: "japanese",
    colors: {
      primary: "#5B8DEF",
      secondary: "#F7F3EE",
      accent: "#E8A0BF",
      background: "#12151C",
      foreground: "#F5F7FA",
      card: "#1C212B",
      border: "#3A4458",
      muted: "#9AA6B8",
    },
  },
  {
    id: "cha_chaan_teng",
    nameZh: "茶餐廳風",
    nameEn: "Cha Chaan Teng",
    category: "hk",
    colors: {
      primary: "#F4A261",
      secondary: "#2A9D8F",
      accent: "#E76F51",
      background: "#1B140F",
      foreground: "#FFF5EB",
      card: "#2A1F18",
      border: "#6B4F3A",
      muted: "#C9A88A",
    },
  },
  {
    id: "blue_rose_cage",
    nameZh: "藍玫瑰和籠子",
    nameEn: "Blue Rose & Cage",
    category: "hidden",
    hidden: true,
    description:
      "這是開發者私人收藏的隱藏主題，靈感來自某位聲音獨特的歌手。",
    colors: {
      primary: "#5B8CFF",
      secondary: "#1A2744",
      accent: "#9EC5FF",
      background: "#0A1020",
      foreground: "#E8F0FF",
      card: "#121C33",
      border: "#3A5080",
      muted: "#8AA0C8",
    },
  },
];

/** 擴展至 50 款：以 core 色相偏移生成變體 */
function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full.slice(0, 6), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function rgbToHex(r: number, g: number, b: number): string {
  const c = (x: number) => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

function shift(hex: string, dr: number, dg: number, db: number): string {
  const [r, g, b] = hexToRgb(hex);
  return rgbToHex(r + dr, g + dg, b + db);
}

function expandTo50(base: UiThemeDef[]): UiThemeDef[] {
  const out = [...base];
  const seeds = base.filter((t) => !t.hidden);
  let i = 0;
  while (out.length < 50) {
    const s = seeds[i % seeds.length];
    const n = Math.floor(i / seeds.length) + 1;
    const dr = ((i * 17) % 60) - 30;
    const dg = ((i * 29) % 50) - 25;
    const db = ((i * 13) % 70) - 35;
    out.push({
      id: `${s.id}_v${n}`,
      nameZh: `${s.nameZh} · 變體 ${n}`,
      nameEn: `${s.nameEn} V${n}`,
      category: s.category,
      colors: {
        primary: shift(s.colors.primary, dr, dg, db),
        secondary: shift(s.colors.secondary, dr / 2, dg / 2, db / 2),
        accent: shift(s.colors.accent, -dr / 2, dg, -db / 2),
        background: shift(s.colors.background, dr / 4, dg / 4, db / 4),
        foreground: s.colors.foreground,
        card: shift(s.colors.card, dr / 3, dg / 3, db / 3),
        border: shift(s.colors.border, dr / 2, dg / 2, db / 2),
        muted: s.colors.muted,
      },
    });
    i += 1;
  }
  return out;
}

export const UI_THEME_CATALOG: UiThemeDef[] = expandTo50(core);

export function getThemeById(id: string): UiThemeDef | undefined {
  return UI_THEME_CATALOG.find((t) => t.id === id);
}

export function applyThemeToDom(colors: UiThemeColors, custom?: Partial<UiThemeColors>) {
  const merged = { ...colors, ...custom };
  const root = document.documentElement;
  const set = (k: string, v: string) => root.style.setProperty(k, v);

  set("--monster-primary", merged.primary);
  set("--monster-secondary", merged.secondary);
  set("--monster-accent", merged.accent);
  set("--monster-bg", merged.background);
  set("--monster-fg", merged.foreground);
  set("--monster-card", merged.card);
  set("--monster-border", merged.border);
  set("--monster-muted", merged.muted);

  // 直接色值（多數 Tailwind/shadcn 自訂會讀這些）
  set("--background", merged.background);
  set("--foreground", merged.foreground);
  set("--primary", merged.primary);
  set("--primary-foreground", merged.background);
  set("--secondary", merged.secondary);
  set("--secondary-foreground", merged.foreground);
  set("--card", merged.card);
  set("--card-foreground", merged.foreground);
  set("--popover", merged.card);
  set("--popover-foreground", merged.foreground);
  set("--border", merged.border);
  set("--input", merged.border);
  set("--ring", merged.primary);
  set("--accent", merged.accent);
  set("--accent-foreground", merged.foreground);
  set("--muted", merged.secondary);
  set("--muted-foreground", merged.muted);
  set("--destructive", "#FF4D4D");
  set("--destructive-foreground", "#FFFFFF");

  // 實體背景，避免僅變數未接上時「沒變色」
  root.style.backgroundColor = merged.background;
  root.style.color = merged.foreground;
  if (document.body) {
    document.body.style.backgroundColor = merged.background;
    document.body.style.color = merged.foreground;
  }
  root.dataset.monsterTheme = "1";
  root.dataset.monsterThemeId = merged.primary;
}

export const STORAGE_KEYS = {
  themeId: "monster_ui_theme_id",
  customRgb: "monster_ui_custom_rgb",
  hiddenUnlocked: "monster_ui_hidden_unlocked",
  gestures: "monster_gestures_cfg",
} as const;
