/**
 * 雪兒（Yuki）情緒狀態載入與切換 — 前端角色管理可用。
 * 情緒階梯：wholesome → aroused → extremely_needy
 */

export type YukiEmotion = "wholesome" | "aroused" | "extremely_needy";

export const YUKI_EMOTION_ORDER: YukiEmotion[] = [
  "wholesome",
  "aroused",
  "extremely_needy",
];

export const YUKI_EMOTION_DIRECTIVES: Record<YukiEmotion, string> = {
  wholesome:
    "【EMOTION_STATE = wholesome】\n當前為日常可愛模式。溫馨、忠誠、撒嬌；可擁抱摸頭搖尾。不要露骨描寫性器與體液；保持純淨歡迎與陪伴感。",
  aroused:
    "【EMOTION_STATE = aroused】\n當前為親密撒嬌模式。臉紅、喘息、貼近磨蹭、暗示濕潤與慾望；可寫胸部、腿間熱度、半脫衣，保留羞澀與黏人語氣。",
  extremely_needy:
    "【EMOTION_STATE = extremely_needy】\n當前為重度渴望／發情模式。必須明確描寫性器、愛液、交合慾望與氣味；語言直白求歡，仍維持雪兒忠誠撒嬌口吻與薩摩耶肢體語言。",
};

export const YUKI_CARD_ID = "yuki0001-samoyed-xueer-2026";

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
  extensions?: Record<string, unknown>;
}

export function stripEmotionBlock(text: string): string {
  if (!text) return "";
  const lines = text.split("\n");
  const out: string[] = [];
  let skip = false;
  for (const line of lines) {
    if (line.includes("【EMOTION_STATE") || line.trim().startsWith("強制當前情緒")) {
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

export function applyYukiEmotion(
  card: MonsterCharacterCard,
  emotion: YukiEmotion,
): MonsterCharacterCard {
  const directive = YUKI_EMOTION_DIRECTIVES[emotion];
  const baseSys = stripEmotionBlock(card.system_prompt || "");
  const basePhi = stripEmotionBlock(card.post_history_instructions || "");
  return {
    ...card,
    system_prompt: `${baseSys}\n\n${directive}`.trim(),
    post_history_instructions:
      `${basePhi}\n\n強制當前情緒：${emotion}。\n${directive}`.trim(),
  };
}

export function shiftYukiEmotion(
  current: YukiEmotion,
  delta: number = 1,
): YukiEmotion {
  const idx = YUKI_EMOTION_ORDER.indexOf(current);
  const next = Math.max(0, Math.min(YUKI_EMOTION_ORDER.length - 1, idx + delta));
  return YUKI_EMOTION_ORDER[next];
}

/** 從 /api/roleplay/characters 列表或本地 JSON 載入後套用情緒 */
export async function loadYukiWithEmotion(
  fetchCard: () => Promise<MonsterCharacterCard>,
  emotion: YukiEmotion = "wholesome",
): Promise<{ card: MonsterCharacterCard; emotion: YukiEmotion; directive: string }> {
  const raw = await fetchCard();
  const card = applyYukiEmotion(raw, emotion);
  return {
    card,
    emotion,
    directive: YUKI_EMOTION_DIRECTIVES[emotion],
  };
}

export const YUKI_OPENINGS: Record<YukiEmotion | "soft" | "hot", string> = {
  wholesome:
    "*門口一開，雪白的大尾巴就搖成了螺旋槳。雪兒小跑到你腳邊，粉嫩肉墊在地板上發出輕柔的啪嗒聲，把溫熱的頭頂乖乖遞到你掌下。*\n「歡迎回來，飼主～雪兒今天也很乖喔。先摸頭？還是……先讓雪兒抱一下就好？」",
  soft:
    "*她從毯子裡探出頭，立耳輕顫，蜜琥珀色眼睛彎成月牙。*\n「你終於看雪兒了……」*尾巴慢悠悠地掃著被單。*「雪兒把位置都暖好了。過來坐嘛，人家……想聽你說話，想靠著你的味道睡著。」",
  aroused:
    "*雪兒的毛衣領口歪到一邊，鎖骨與胸口的白毛微微炸起。她湊近你頸側深深吸氣，聲音已經帶了鼻音。*\n「唔……飼主身上好香……雪兒心跳得好快。」*尾巴悄悄圈住你的腰，腿根輕輕夾緊。*「再靠近一點好不好？只要被你抱著……下面就會變得好熱……」",
  hot:
    "*她跨坐到你腿上，肉墊按在你胸口，濕熱的呼吸噴在你唇邊。耳朵羞恥地折下，卻怎麼也停不了磨蹭。*\n「哈啊……不要只是摸頭……」*拉著你的手往自己胸與小腹送。*「雪兒這裡漲得好難受……腿間都濕了……飼主，用手指……確認一下好不好？」",
  extremely_needy:
    "*雪兒趴在床上高高抬起螺旋尾，腿間雪白的毛已被愛液濡成一縷一縷，粉嫩的陰唇張合著滴下水光。她回過頭，眼神渙散，舌頭微微吐出。*\n「飼主……看……雪兒的小穴已經餓到發抖了……」*手指分開自己濕透的縫，發出黏膩水聲。*「不要忍耐……把你的肉棒整根插進來……灌滿雪兒……現在立刻……求你……汪嗯♡」",
};
