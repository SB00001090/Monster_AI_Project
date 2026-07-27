"""
情緒自學分析 + 自行生成對話提示
開發者：suckbob | 發行商：Monster_Ai_hk

- 即時分析用戶輸入（台灣口語 + 香港粵語口語）
- 輸出標準格式：（情緒）原始文字
- 產生 suggested_dialogue_hint 注入 LLM
- 寫入 data/learning/emotion_learning.jsonl
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# 情緒標籤（標準集合）
EMOTIONS = (
    "開心",
    "興奮",
    "撒嬌",
    "傲嬌",
    "平靜",
    "難過",
    "生氣",
    "焦慮",
    "害羞",
    "慾求",
    "疲累",
    "好奇",
    "無聊",
    "溫柔",
    "中性",
)


@dataclass
class EmotionResult:
    emotion: str
    tagged_text: str  # （情緒）原始文字
    confidence: float
    dialect: str  # tw | hk | mixed | unknown
    signals: list[str] = field(default_factory=list)
    suggested_dialogue_hint: str = ""
    llm_system_inject: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# 台灣口語訊號
_TW_SIGNALS: dict[str, list[str]] = {
    "開心": ["超開心", "好爽", "讚啦", "太棒了", "開心死", "耶", "哈哈哈", "好笑", "爽"],
    "興奮": ["興奮", "迫不及待", "超期待", "衝啊", "發了", "幹起來"],
    "撒嬌": ["啦～", "嘛", "好不好嘛", "拜託啦", "人家", "嗚嗚", "哼嗯"],
    "傲嬌": ["才不是", "才沒有", "哼", "隨便你", "不關你的事", "笨蛋"],
    "難過": ["好難過", "想哭", "心碎", "低落", "郁闷", "唉", "崩潰"],
    "生氣": ["氣死", "幹", "靠北", "惱火", "火大", "氣炸", "他媽"],
    "焦慮": ["好緊張", "慌", "擔心", "不安", "焦慮", "怎麼辦"],
    "害羞": ["好害羞", "丟臉", "臉紅", "不要看", "說不出口"],
    "慾求": ["想要", "好想", "忍不住", "發熱", "色色", "想抱", "想摸", "硬了", "濕了"],
    "疲累": ["好累", "累爆", "想睡", "沒電", "撐不住"],
    "好奇": ["蛤", "什麼意思", "怎麼了", "是怎樣", "告訴我"],
    "無聊": ["好無聊", "沒意思", "沒事做", "閒閒"],
    "溫柔": ["謝謝你", "辛苦了", "慢慢來", "沒關係", "我在"],
}

# 香港粵語口語訊號
_HK_SIGNALS: dict[str, list[str]] = {
    "開心": ["好開心", "正呀", "掂呀", "勁呀", "開心到飛起", "哈哈", "笑死"],
    "興奮": ["興奮", "等唔切", "搏命", "衝呀", "上呀"],
    "撒嬌": ["啦～", "好唔好呀", "求下你", "哎呀", "嗯嗯"],
    "傲嬌": ["先唔係", "關你事", "哼", "隨便你啦", "痴線"],
    "難過": ["好傷心", "喊", "心痛", "唔開心", "慘過"],
    "生氣": ["嬲", "滾", "仆街", "氣死", "攞命", "痴線架"],
    "焦慮": ["好緊張", "驚", "擔心", "點算", "焦慮"],
    "害羞": ["好羞家", "面紅", "唔好望", "講唔出口"],
    "慾求": ["想要", "好想", "忍唔住", "想錫", "想攬", "興奮到"],
    "疲累": ["好攰", "攰爆", "想瞓", "冇電", "頂唔順"],
    "好奇": ["吓", "咩意思", "點解", "係咩", "講下"],
    "無聊": ["好悶", "冇癮", "冇嘢做", "得閒"],
    "溫柔": ["多謝你", "辛苦晒", "慢慢嚟", "冇事", "我喺度"],
}

# 粵語特有字元（粗略方言偵測）
_HK_CHARS = re.compile(r"[喺嘅咗嚟冇係咩嗰啲咁嘞喎噃]")


class EmotionAnalyzer:
    """規則 + 權重情緒分析器（本地、低延遲，可接 LLM 加強）。"""

    def __init__(
        self,
        *,
        data_dir: str | Path = "./data/learning",
        enabled: bool = True,
        log_emotion_tag: bool = True,
        influence_response: bool = True,
        save_to_training: bool = True,
    ) -> None:
        self.enabled = enabled
        self.log_emotion_tag = log_emotion_tag
        self.influence_response = influence_response
        self.save_to_training = save_to_training
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.data_dir / "emotion_learning.jsonl"

    def analyze(self, text: str) -> EmotionResult:
        raw = (text or "").strip()
        if not raw or not self.enabled:
            return EmotionResult(
                emotion="中性",
                tagged_text=f"（中性）{raw}",
                confidence=0.0,
                dialect="unknown",
                suggested_dialogue_hint="以平穩、自然語氣回應。",
                llm_system_inject="",
            )

        dialect = self._detect_dialect(raw)
        scores: dict[str, float] = {e: 0.0 for e in EMOTIONS}
        hits: list[str] = []

        sources = []
        if dialect in ("tw", "mixed", "unknown"):
            sources.append(("tw", _TW_SIGNALS))
        if dialect in ("hk", "mixed", "unknown"):
            sources.append(("hk", _HK_SIGNALS))
        if not sources:
            sources = [("tw", _TW_SIGNALS), ("hk", _HK_SIGNALS)]

        lower = raw.lower()
        for _tag, table in sources:
            for emotion, phrases in table.items():
                for p in phrases:
                    if p.lower() in lower or p in raw:
                        # 較長片語權重更高，避免單字「點算」蓋過「好攰」
                        w = 1.0 + min(len(p), 8) * 0.12
                        scores[emotion] = scores.get(emotion, 0.0) + w
                        hits.append(f"{emotion}:{p}")

        # 標點 / 語氣加強
        if "！" in raw or "!" in raw:
            scores["興奮"] += 0.3
            scores["生氣"] += 0.15
        if "？" in raw or "?" in raw:
            scores["好奇"] += 0.35
        if "…" in raw or "..." in raw:
            scores["難過"] += 0.2
            scores["疲累"] += 0.15
        if re.search(r"[哈嘿呵]{2,}|www+|哈哈哈|嘻嘻", raw, re.I):
            scores["開心"] += 0.8

        # 疲累優先：攰/累/沒電 出現時壓過純「點算」焦慮
        if any(k in raw for k in ("攰", "好累", "累爆", "沒電", "冇電", "想瞓", "想睡")):
            scores["疲累"] += 1.6
            scores["焦慮"] = max(0.0, scores.get("焦慮", 0.0) - 0.5)

        # 極短句（≤2 字）且無明顯命中 → 中性，避免誤判
        strong_hit = any(scores.get(e, 0) >= 1.0 for e in EMOTIONS if e != "中性")
        if len(raw) <= 2 and not strong_hit:
            scores = {e: 0.0 for e in EMOTIONS}
            scores["中性"] = 1.0

        # 預設中性底分
        scores["中性"] += 0.15
        emotion = max(scores, key=lambda k: scores[k])
        best = scores[emotion]
        total = sum(scores.values()) or 1.0
        confidence = min(0.99, best / total + 0.2) if best > 0.2 else 0.35
        if best < 0.25:
            emotion = "中性"
            confidence = 0.4

        tagged = f"（{emotion}）{raw}" if self.log_emotion_tag else raw
        hint = self._dialogue_hint(emotion, dialect, raw)
        inject = ""
        if self.influence_response:
            inject = (
                f"[情緒自學] 用戶當前情緒：{emotion}（信心 {confidence:.2f}，方言傾向 {dialect}）。\n"
                f"標記輸入：{tagged}\n"
                f"請自行生成符合此情緒的角色對話，不要只複讀提示。\n"
                f"對話方向建議：{hint}\n"
                f"使用自然台灣華語或香港粵語口語（依用戶用詞混搭），保持角色人設。"
            )

        result = EmotionResult(
            emotion=emotion,
            tagged_text=tagged,
            confidence=round(confidence, 3),
            dialect=dialect,
            signals=hits[:12],
            suggested_dialogue_hint=hint,
            llm_system_inject=inject,
        )
        if self.save_to_training:
            self._append_log(result, raw)
        return result

    def _detect_dialect(self, text: str) -> str:
        hk = bool(_HK_CHARS.search(text)) or any(
            w in text for w in ("喺", "冇", "係咩", "點解", "仆街", "正呀", "攰", "嚟")
        )
        tw = any(w in text for w in ("幹", "靠北", "超", "欸", "啦", "齁", "ㄟ", "讚啦", "氣死"))
        if hk and tw:
            return "mixed"
        if hk:
            return "hk"
        if tw:
            return "tw"
        return "unknown"

    def _dialogue_hint(self, emotion: str, dialect: str, raw: str) -> str:
        locale = {
            "tw": "台灣口語",
            "hk": "香港粵語口語",
            "mixed": "台港口語混搭",
            "unknown": "自然中文口語",
        }.get(dialect, "自然中文口語")

        table = {
            "開心": f"用輕快、會心一笑的{locale}回應，可適度玩笑，延續用戶好心情。",
            "興奮": f"提高能量與節奏，{locale}要帶衝勁，一起期待下一拍。",
            "撒嬌": f"用寵溺、軟語{locale}接住撒嬌，可回以親暱動作描述。",
            "傲嬌": f"先別戳破，用帶刺但關心的{locale}接話，慢慢軟化。",
            "難過": f"先共情、放慢語氣，{locale}溫柔陪伴，勿急著講大道理。",
            "生氣": f"承認情緒、勿火上加油；用穩的{locale}協助降溫或一起吐槽對象。",
            "焦慮": f"安撫＋具體小步驟；{locale}清楚、簡短、給安全感。",
            "害羞": f"輕聲調侃但留面子，{locale}別過度逼問。",
            "慾求": f"在角色與安全框架內以直白、感官細節的{locale}回應親密氛圍（成人虛構）。",
            "疲累": f"放慢節奏、關心休息，{locale}溫暖短句。",
            "好奇": f"解答或一起探索，{locale}清楚有趣。",
            "無聊": f"拋有趣話題或小互動，{locale}活潑一些。",
            "溫柔": f"回以同等溫柔與感謝，{locale}安定。",
            "中性": f"自然對話，觀察用戶下一句再調整；{locale}。",
            "平靜": f"平穩交流，{locale}舒適。",
        }
        base = table.get(emotion, table["中性"])
        return f"{base} 勿忽略用戶原意：「{raw[:80]}」"

    def _append_log(self, result: EmotionResult, raw: str) -> None:
        try:
            row = {
                "ts": time.time(),
                "raw": raw,
                **result.to_dict(),
                "developer": "suckbob",
                "publisher": "Monster_Ai_hk",
            }
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
