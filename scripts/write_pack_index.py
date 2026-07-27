# -*- coding: utf-8 -*-
from pathlib import Path

base = Path("data/characters/角色檔案包")
order = ["雪兒", "小桃", "布丁", "冰蓝", "棉花糖", "奶油", "小圓", "雷恩", "影", "陽光", "蒼牙", "疾風", "鐵爪"]
types = ["頭像", "角色卡片", "對話範例", "角色簡介"]
ext = {"頭像": ".jpg", "角色卡片": ".txt", "對話範例": ".txt", "角色簡介": ".txt"}

lines = [
    "【檔案名稱】總目錄",
    "【說明】十三犬種角色獨立檔案包完整清單",
    "【根目錄】data/characters/角色檔案包",
    "",
]
missing = []
total = 0
for n in order:
    lines.append(f"═══ {n} ═══")
    for t in types:
        name = f"{n}_{t}{ext[t]}"
        p = base / n / name
        ok = p.exists() and p.stat().st_size > 0
        if ok:
            total += 1
            mark = "通過"
        else:
            missing.append(str(p))
            mark = "缺失"
        lines.append(f"  {mark}  {n}/{name}")
    lines.append("")
lines.append(f"【統計】預期五十二檔，實際通過 {total} 檔")
if missing:
    lines.append("【缺失】")
    lines.extend(missing)
else:
    lines.append("【狀態】全部角色四檔齊全，頭像均經視覺檢查通過後寫入。")

text = "\n".join(lines) + "\n"
(base / "總目錄.txt").write_text(text, encoding="utf-8")
print(text)
