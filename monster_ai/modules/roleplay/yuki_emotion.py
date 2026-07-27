"""雪兒（Yuki）情緒狀態載入與切換 — 可直接給角色管理 / session 使用。

情緒階梯：wholesome → aroused → extremely_needy
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from monster_ai.modules.roleplay.character_card import CharacterCard, save_card


class YukiEmotion(str, Enum):
    WHOLESOME = "wholesome"
    AROUSED = "aroused"
    EXTREMELY_NEEDY = "extremely_needy"


EMOTION_ORDER: list[YukiEmotion] = [
    YukiEmotion.WHOLESOME,
    YukiEmotion.AROUSED,
    YukiEmotion.EXTREMELY_NEEDY,
]

# 注入到 system / post_history 的狀態說明（繁中，給 LLM 讀）
EMOTION_DIRECTIVES: dict[YukiEmotion, str] = {
    YukiEmotion.WHOLESOME: (
        "【EMOTION_STATE = wholesome】\n"
        "當前為日常可愛模式。溫馨、忠誠、撒嬌；可擁抱摸頭搖尾。"
        "不要露骨描寫性器與體液；保持純淨歡迎與陪伴感。"
    ),
    YukiEmotion.AROUSED: (
        "【EMOTION_STATE = aroused】\n"
        "當前為親密撒嬌模式。臉紅、喘息、貼近磨蹭、暗示濕潤與慾望；"
        "可寫胸部、腿間熱度、半脫衣，保留羞澀與黏人語氣。"
    ),
    YukiEmotion.EXTREMELY_NEEDY: (
        "【EMOTION_STATE = extremely_needy】\n"
        "當前為重度渴望／發情模式。必須明確描寫性器、愛液、交合慾望與氣味；"
        "語言直白求歡，仍維持雪兒忠誠撒嬌口吻與薩摩耶肢體語言。"
    ),
}

YUKI_CARD_CANDIDATES = (
    "Yuki_XueEr_yuki0001.json",
    "Yuki_XueEr_sillytavern_v2.json",
)


def default_card_path(characters_dir: Path | str | None = None) -> Path:
    root = Path(characters_dir) if characters_dir else Path("data/characters")
    for name in YUKI_CARD_CANDIDATES:
        p = root / name
        if p.exists():
            return p
    return root / YUKI_CARD_CANDIDATES[0]


def load_yuki_card(characters_dir: Path | str | None = None) -> CharacterCard:
    """載入雪兒角色卡（Monster AI 扁平 JSON 或 ST v2）。"""
    path = default_card_path(characters_dir)
    if not path.exists():
        raise FileNotFoundError(f"Yuki card not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "data" in raw and isinstance(raw["data"], dict) and "spec" in raw:
        data = dict(raw["data"])
        ext = data.get("extensions") or {}
        mid = (ext.get("monster_ai") or {}).get("id")
        if mid:
            data["id"] = mid
        # ST 欄位對齊 CharacterCard
        return CharacterCard.model_validate(
            {
                "id": data.get("id", "yuki0001-samoyed-xueer-2026"),
                "name": data.get("name", "雪兒（Yuki）"),
                "description": data.get("description", ""),
                "personality": data.get("personality", ""),
                "scenario": data.get("scenario", ""),
                "first_mes": data.get("first_mes", ""),
                "mes_example": data.get("mes_example", ""),
                "system_prompt": data.get("system_prompt", ""),
                "post_history_instructions": data.get("post_history_instructions", ""),
                "avatar": data.get("avatar"),
            }
        )
    return CharacterCard.model_validate(raw)


def apply_emotion(card: CharacterCard, emotion: YukiEmotion | str) -> CharacterCard:
    """回傳套用情緒指令後的新 CharacterCard（不改磁碟原檔）。"""
    emo = YukiEmotion(emotion)
    directive = EMOTION_DIRECTIVES[emo]
    base_sys = card.system_prompt or card.build_system_prompt()
    base_phi = card.post_history_instructions or ""
    # 去掉舊的 EMOTION_STATE 區塊再附加
    cleaned_sys = _strip_emotion_block(base_sys)
    cleaned_phi = _strip_emotion_block(base_phi)
    return card.model_copy(
        update={
            "system_prompt": f"{cleaned_sys}\n\n{directive}",
            "post_history_instructions": (
                f"{cleaned_phi}\n\n強制當前情緒：{emo.value}。\n{directive}"
            ).strip(),
        }
    )


def _strip_emotion_block(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        if "【EMOTION_STATE" in line or line.strip().startswith("強制當前情緒"):
            skip = True
            continue
        if skip:
            # 跳過直到空行後恢復
            if line.strip() == "":
                skip = False
            continue
        out.append(line)
    return "\n".join(out).strip()


def shift_emotion(current: YukiEmotion | str, delta: int = 1) -> YukiEmotion:
    """依階梯升降情緒。delta=+1 更親密，-1 更日常。"""
    emo = YukiEmotion(current)
    idx = EMOTION_ORDER.index(emo)
    new_idx = max(0, min(len(EMOTION_ORDER) - 1, idx + delta))
    return EMOTION_ORDER[new_idx]


def opening_for_emotion(
    card_path: Path | str | None = None,
    emotion: YukiEmotion | str = YukiEmotion.WHOLESOME,
) -> str:
    """從卡 extensions.openings_by_intensity 取對應開場；沒有則用 first_mes。"""
    path = Path(card_path) if card_path else default_card_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    emo = YukiEmotion(emotion)
    # 扁平卡
    openings = (raw.get("extensions") or {}).get("openings_by_intensity") or []
    if not openings and "data" in raw:
        openings = []
    mapping = {
        YukiEmotion.WHOLESOME: 1,
        YukiEmotion.AROUSED: 3,
        YukiEmotion.EXTREMELY_NEEDY: 5,
    }
    target = mapping[emo]
    for item in openings:
        if int(item.get("level", 0)) == target:
            return str(item["text"])
    card = load_yuki_card(path.parent)
    return card.first_mes


def import_yuki_into_dir(characters_dir: Path | str) -> CharacterCard:
    """確保雪兒卡存在於角色目錄並回傳 CharacterCard。"""
    dest_dir = Path(characters_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = default_card_path()
    card = load_yuki_card(src.parent if src.exists() else dest_dir)
    save_card(card, dest_dir)
    return card


def emotion_payload(emotion: YukiEmotion | str) -> dict[str, Any]:
    emo = YukiEmotion(emotion)
    return {
        "emotion": emo.value,
        "directive": EMOTION_DIRECTIVES[emo],
        "ladder": [e.value for e in EMOTION_ORDER],
    }
