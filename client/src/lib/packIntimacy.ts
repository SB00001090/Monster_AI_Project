/**
 * 雪兒風格犬種包：角色載入 + 親密度階段切換（前端）
 * wholesome → aroused → extremely_needy
 */

export type IntimacyStage = "wholesome" | "aroused" | "extremely_needy";

export const STAGE_ORDER: IntimacyStage[] = [
  "wholesome",
  "aroused",
  "extremely_needy",
];

export const STAGE_DIRECTIVES: Record<IntimacyStage, string> = {
  wholesome:
    "【INTIMACY_STAGE = wholesome / EMOTION_STATE = wholesome】\n當前為日常可愛模式。溫馨、忠誠、撒嬌；可擁抱摸頭搖尾。不要露骨描寫性器與體液；保持純淨歡迎與陪伴感。",
  aroused:
    "【INTIMACY_STAGE = aroused / EMOTION_STATE = aroused】\n當前為親密模式。臉紅、喘息、貼近磨蹭、暗示濕潤與慾望；可寫肢體熱度與半脫衣，保留一點羞澀或克制。",
  extremely_needy:
    "【INTIMACY_STAGE = extremely_needy / EMOTION_STATE = extremely_needy】\n當前為重度渴望／R18 模式。必須明確描寫性器、體液、交合慾望與氣味；語言直白求歡，仍維持該角色品種口吻與肢體語言。",
};

export const PACK_SLUGS = [
  "yuki_xueer",
  "xiaotao_shiba",
  "buding_corgi",
  "binglan_husky",
  "lein_gsd",
  "ying_doberman",
  "yangguang_golden",
] as const;

export type PackSlug = (typeof PACK_SLUGS)[number];

export const PACK_ALIASES: Record<string, PackSlug> = {
  雪兒: "yuki_xueer",
  yuki: "yuki_xueer",
  小桃: "xiaotao_shiba",
  布丁: "buding_corgi",
  冰蓝: "binglan_husky",
  雷恩: "lein_gsd",
  影: "ying_doberman",
  陽光: "yangguang_golden",
};

export interface MonsterCharacterCard {
  id: string;
  name: string;
  description: string;
  personality: string;
  scenario: string;
  first_mes: string;
  mes_example?: string;
  system_prompt: string;
  post_history_instructions?: string;
  avatar?: string | null;
  extensions?: {
    monster_ai?: Record<string, unknown>;
    image_prompts?: Record<string, { positive?: string; negative?: string }>;
    openings_by_intensity?: Array<{ level?: number; emotion?: string; text: string }>;
  };
}

export function resolveSlug(nameOrSlug: string): PackSlug {
  if ((PACK_SLUGS as readonly string[]).includes(nameOrSlug)) {
    return nameOrSlug as PackSlug;
  }
  const alias = PACK_ALIASES[nameOrSlug];
  if (alias) return alias;
  throw new Error(`Unknown pack character: ${nameOrSlug}`);
}

export function stripStageBlock(text: string): string {
  if (!text) return "";
  const lines = text.split("\n");
  const out: string[] = [];
  let skip = false;
  for (const line of lines) {
    if (
      line.includes("【INTIMACY_STAGE") ||
      line.includes("【EMOTION_STATE") ||
      line.trim().startsWith("強制當前")
    ) {
      skip = true;
      continue;
    }
    if (skip) {
      if (line.trim() === "") skip = false;
      continue;
    }
    out.push(line);
  }
  return out.join("\n").trim();
}

export function applyIntimacy(
  card: MonsterCharacterCard,
  stage: IntimacyStage,
): MonsterCharacterCard {
  const directive = STAGE_DIRECTIVES[stage];
  const baseSys = stripStageBlock(card.system_prompt || "");
  const basePhi = stripStageBlock(card.post_history_instructions || "");
  return {
    ...card,
    system_prompt: `${baseSys}\n\n${directive}`.trim(),
    post_history_instructions:
      `${basePhi}\n\n強制當前親密度：${stage}。\n${directive}`.trim(),
  };
}

export function shiftIntimacy(
  current: IntimacyStage,
  delta: number = 1,
): IntimacyStage {
  const idx = STAGE_ORDER.indexOf(current);
  const next = Math.max(0, Math.min(STAGE_ORDER.length - 1, idx + delta));
  return STAGE_ORDER[next];
}

export function openingFor(
  card: MonsterCharacterCard,
  stage: IntimacyStage,
): string {
  const openings = card.extensions?.openings_by_intensity || [];
  const preferLevel: Record<IntimacyStage, number[]> = {
    wholesome: [1],
    aroused: [2, 3],
    extremely_needy: [3, 5],
  };
  for (const level of preferLevel[stage]) {
    const hit = openings.find(
      (o) => o.level === level || o.emotion === stage || o.emotion?.includes(stage),
    );
    if (hit?.text) return hit.text;
  }
  const byEmotion = openings.find((o) => o.emotion === stage);
  if (byEmotion?.text) return byEmotion.text;
  return card.first_mes;
}

export function imagePromptsFor(
  card: MonsterCharacterCard,
  stage: IntimacyStage,
): { positive: string; negative: string } {
  const block = card.extensions?.image_prompts?.[stage] ||
    card.extensions?.image_prompts?.wholesome ||
    {};
  return {
    positive: block.positive || "",
    negative: block.negative || "",
  };
}

/** 從角色列表 / 本機 JSON 載入後套用親密度 */
export async function bootstrapPackCharacter(
  fetchCard: () => Promise<MonsterCharacterCard>,
  stage: IntimacyStage = "wholesome",
): Promise<{
  card: MonsterCharacterCard;
  stage: IntimacyStage;
  directive: string;
  opening: string;
  imagePrompts: { positive: string; negative: string };
}> {
  const raw = await fetchCard();
  const card = applyIntimacy(raw, stage);
  return {
    card,
    stage,
    directive: STAGE_DIRECTIVES[stage],
    opening: openingFor(raw, stage),
    imagePrompts: imagePromptsFor(raw, stage),
  };
}
