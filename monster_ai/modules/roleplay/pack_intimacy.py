"""雪兒風格犬種包：角色載入 + 親密度階段切換。

階段階梯（與雪兒一致）：
  wholesome → aroused → extremely_needy

可用 slug：
  yuki_xueer, xiaotao_shiba, buding_corgi, binglan_husky,
  lein_gsd, ying_doberman, yangguang_golden
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from monster_ai.modules.roleplay.character_card import CharacterCard, save_card

# 可選：與舊雪兒模組相容
try:
    from monster_ai.modules.roleplay.yuki_emotion import YukiEmotion as _YukiEmotion
except Exception:  # pragma: no cover
    _YukiEmotion = None  # type: ignore


class IntimacyStage(str, Enum):
    WHOLESOME = "wholesome"
    AROUSED = "aroused"
    EXTREMELY_NEEDY = "extremely_needy"


STAGE_ORDER: list[IntimacyStage] = [
    IntimacyStage.WHOLESOME,
    IntimacyStage.AROUSED,
    IntimacyStage.EXTREMELY_NEEDY,
]

STAGE_DIRECTIVES: dict[IntimacyStage, str] = {
    IntimacyStage.WHOLESOME: (
        "【INTIMACY_STAGE = wholesome / EMOTION_STATE = wholesome】\n"
        "當前為日常可愛模式。溫馨、忠誠、撒嬌；可擁抱摸頭搖尾。"
        "不要露骨描寫性器與體液；保持純淨歡迎與陪伴感。"
    ),
    IntimacyStage.AROUSED: (
        "【INTIMACY_STAGE = aroused / EMOTION_STATE = aroused】\n"
        "當前為親密模式。臉紅、喘息、貼近磨蹭、暗示濕潤與慾望；"
        "可寫肢體熱度與半脫衣，保留一點羞澀或克制。"
    ),
    IntimacyStage.EXTREMELY_NEEDY: (
        "【INTIMACY_STAGE = extremely_needy / EMOTION_STATE = extremely_needy】\n"
        "當前為重度渴望／R18 模式。必須明確描寫性器、體液、交合慾望與氣味；"
        "語言直白求歡，仍維持該角色品種口吻與肢體語言。"
    ),
}

# slug -> 檔名（扁平 Monster AI 卡）
PACK_FILES: dict[str, str] = {
    "yuki_xueer": "Yuki_XueEr_yuki0001.json",
    "xiaotao_shiba": "Xiaotao_Shiba_peach0001.json",
    "buding_corgi": "Buding_Corgi_pudding0001.json",
    "binglan_husky": "Binglan_Husky_iceblue0001.json",
    "lein_gsd": "Lein_GSD_rain0001.json",
    "ying_doberman": "Ying_Doberman_shadow0001.json",
    "yangguang_golden": "Yangguang_Golden_sunny0001.json",
}

# 別名
PACK_ALIASES: dict[str, str] = {
    "雪兒": "yuki_xueer",
    "yuki": "yuki_xueer",
    "小桃": "xiaotao_shiba",
    "布丁": "buding_corgi",
    "冰蓝": "binglan_husky",
    "雷恩": "lein_gsd",
    "影": "ying_doberman",
    "陽光": "yangguang_golden",
}


def resolve_slug(name_or_slug: str) -> str:
    key = name_or_slug.strip()
    if key in PACK_FILES:
        return key
    if key in PACK_ALIASES:
        return PACK_ALIASES[key]
    lower = key.lower()
    for slug in PACK_FILES:
        if slug == lower or slug.replace("_", "") == lower.replace("_", "").replace("-", ""):
            return slug
    raise KeyError(f"Unknown pack character: {name_or_slug!r}. Known: {list(PACK_FILES)}")


def characters_dir(base: Path | str | None = None) -> Path:
    return Path(base) if base else Path("data/characters")


def load_pack_card(name_or_slug: str, base: Path | str | None = None) -> CharacterCard:
    """載入雪兒風格犬種包角色卡。"""
    slug = resolve_slug(name_or_slug)
    path = characters_dir(base) / PACK_FILES[slug]
    if not path.exists():
        raise FileNotFoundError(f"Card not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "data" in raw and isinstance(raw.get("data"), dict) and raw.get("spec"):
        data = dict(raw["data"])
        mid = ((data.get("extensions") or {}).get("monster_ai") or {}).get("id")
        return CharacterCard.model_validate(
            {
                "id": mid or data.get("id", slug),
                "name": data.get("name", slug),
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


def load_pack_raw(name_or_slug: str, base: Path | str | None = None) -> dict[str, Any]:
    slug = resolve_slug(name_or_slug)
    path = characters_dir(base) / PACK_FILES[slug]
    return json.loads(path.read_text(encoding="utf-8"))


def strip_stage_block(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    out: list[str] = []
    skip = False
    for line in lines:
        if (
            "【INTIMACY_STAGE" in line
            or "【EMOTION_STATE" in line
            or line.strip().startswith("強制當前")
        ):
            skip = True
            continue
        if skip:
            if line.strip() == "":
                skip = False
            continue
        out.append(line)
    return "\n".join(out).strip()


def apply_intimacy(
    card: CharacterCard,
    stage: IntimacyStage | str,
) -> CharacterCard:
    """回傳套用親密度指令後的新卡（不改磁碟）。"""
    emo = IntimacyStage(stage)
    directive = STAGE_DIRECTIVES[emo]
    base_sys = strip_stage_block(card.system_prompt or card.build_system_prompt())
    base_phi = strip_stage_block(card.post_history_instructions or "")
    return card.model_copy(
        update={
            "system_prompt": f"{base_sys}\n\n{directive}",
            "post_history_instructions": (
                f"{base_phi}\n\n強制當前親密度：{emo.value}。\n{directive}"
            ).strip(),
        }
    )


def shift_intimacy(current: IntimacyStage | str, delta: int = 1) -> IntimacyStage:
    emo = IntimacyStage(current)
    idx = STAGE_ORDER.index(emo)
    new_idx = max(0, min(len(STAGE_ORDER) - 1, idx + delta))
    return STAGE_ORDER[new_idx]


def opening_for(
    name_or_slug: str,
    stage: IntimacyStage | str = IntimacyStage.WHOLESOME,
    base: Path | str | None = None,
) -> str:
    raw = load_pack_raw(name_or_slug, base)
    emo = IntimacyStage(stage)
    openings = (raw.get("extensions") or {}).get("openings_by_intensity") or []
    mapping = {
        IntimacyStage.WHOLESOME: 1,
        IntimacyStage.AROUSED: 2,
        IntimacyStage.EXTREMELY_NEEDY: 3,
    }
    target = mapping[emo]
    for item in openings:
        if int(item.get("level", 0)) == target or item.get("emotion") == emo.value:
            return str(item["text"])
    # 雪兒卡有 5 級，兼容 level 1/3/5
    legacy = {IntimacyStage.WHOLESOME: 1, IntimacyStage.AROUSED: 3, IntimacyStage.EXTREMELY_NEEDY: 5}
    t2 = legacy[emo]
    for item in openings:
        if int(item.get("level", 0)) == t2:
            return str(item["text"])
    return load_pack_card(name_or_slug, base).first_mes


def image_prompts_for(
    name_or_slug: str,
    stage: IntimacyStage | str = IntimacyStage.WHOLESOME,
    base: Path | str | None = None,
) -> dict[str, str]:
    raw = load_pack_raw(name_or_slug, base)
    emo = IntimacyStage(stage)
    prompts = (raw.get("extensions") or {}).get("image_prompts") or {}
    block = prompts.get(emo.value) or prompts.get("wholesome") or {}
    return {
        "positive": str(block.get("positive", "")),
        "negative": str(block.get("negative", "")),
    }


def list_pack(base: Path | str | None = None) -> list[dict[str, Any]]:
    out = []
    root = characters_dir(base)
    for slug, fname in PACK_FILES.items():
        path = root / fname
        if not path.exists():
            out.append({"slug": slug, "file": fname, "available": False})
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        out.append(
            {
                "slug": slug,
                "id": raw.get("id"),
                "name": raw.get("name"),
                "file": fname,
                "available": True,
                "gender": ((raw.get("extensions") or {}).get("monster_ai") or {}).get("gender"),
                "breed": ((raw.get("extensions") or {}).get("monster_ai") or {}).get("breed"),
            }
        )
    return out


def import_all_into(dest: Path | str) -> list[CharacterCard]:
    """把包內所有可用卡寫入指定角色目錄。"""
    dest_dir = Path(dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    cards: list[CharacterCard] = []
    for slug, fname in PACK_FILES.items():
        src = characters_dir() / fname
        if not src.exists():
            continue
        card = load_pack_card(slug)
        save_card(card, dest_dir)
        cards.append(card)
    return cards


def session_bootstrap(
    name_or_slug: str,
    stage: IntimacyStage | str = IntimacyStage.WHOLESOME,
    base: Path | str | None = None,
) -> dict[str, Any]:
    """一次拿齊：角色卡、階段指令、開場白、圖像 prompt。"""
    slug = resolve_slug(name_or_slug)
    emo = IntimacyStage(stage)
    card = apply_intimacy(load_pack_card(slug, base), emo)
    return {
        "slug": slug,
        "stage": emo.value,
        "card": card.model_dump(),
        "directive": STAGE_DIRECTIVES[emo],
        "opening": opening_for(slug, emo, base),
        "image_prompts": image_prompts_for(slug, emo, base),
        "ladder": [s.value for s in STAGE_ORDER],
    }
