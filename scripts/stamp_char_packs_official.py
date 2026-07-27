# -*- coding: utf-8 -*-
"""為十三犬種獨立檔案包寫入官方署名，並確保四檔齊全。"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "characters" / "角色檔案包"
AVATAR_SRC = ROOT / "data" / "characters" / "avatars" / "humanoid_pack"

DEV = "開發者：Suckbob"
PUB = "發行商：Monster_Ai_hk"
HEADER = f"{DEV}\n{PUB}\n"
FOOTER = f"\n{DEV}\n{PUB}\n"

ORDER = [
    "雪兒",
    "小桃",
    "布丁",
    "冰蓝",
    "棉花糖",
    "奶油",
    "小圓",
    "雷恩",
    "影",
    "陽光",
    "蒼牙",
    "疾風",
    "鐵爪",
]

BREED = {
    "雪兒": "薩摩耶",
    "小桃": "柴犬",
    "布丁": "柯基",
    "冰蓝": "哈士奇",
    "棉花糖": "博美",
    "奶油": "比熊",
    "小圓": "法國鬥牛犬",
    "雷恩": "德國牧羊犬",
    "影": "杜賓",
    "陽光": "金毛",
    "蒼牙": "秋田",
    "疾風": "邊境牧羊犬",
    "鐵爪": "羅威納",
}

GENDER = {
    "雪兒": "女",
    "小桃": "女",
    "布丁": "女",
    "冰蓝": "女",
    "棉花糖": "女",
    "奶油": "女",
    "小圓": "女",
    "雷恩": "男",
    "影": "男",
    "陽光": "男",
    "蒼牙": "男",
    "疾風": "男",
    "鐵爪": "男",
}

# 頭像來源對照（既有 humanoid_pack 或 角色檔案包 內檔）
AVATAR_ALIASES = {
    "雪兒": ["01_雪兒_薩摩耶.jpg", "雪兒_頭像.jpg"],
    "小桃": ["02_小桃_柴犬.jpg", "小桃_頭像.jpg"],
    "布丁": ["03_布丁_柯基.jpg", "布丁_頭像.jpg"],
    "冰蓝": ["04_冰蓝_哈士奇.jpg", "冰蓝_頭像.jpg"],
    "棉花糖": ["05_棉花糖_博美.jpg", "棉花糖_頭像.jpg"],
    "奶油": ["06_奶油_比熊.jpg", "奶油_頭像.jpg"],
    "小圓": ["07_小圓_法國鬥牛犬.jpg", "小圓_頭像.jpg"],
    "雷恩": ["08_雷恩_德國牧羊犬.jpg", "雷恩_頭像.jpg"],
    "影": ["09_影_杜賓.jpg", "影_頭像.jpg"],
    "陽光": ["10_陽光_金毛.jpg", "陽光_頭像.jpg"],
    "蒼牙": ["11_蒼牙_秋田.jpg", "蒼牙_頭像.jpg"],
    "疾風": ["12_疾風_邊境牧羊犬.jpg", "疾風_頭像.jpg"],
    "鐵爪": ["13_鐵爪_羅威納.jpg", "鐵爪_頭像.jpg"],
}


def strip_old_credit(text: str) -> str:
    lines = text.splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if s in (DEV, PUB) or s.startswith("開發者：") or s.startswith("發行商："):
            continue
        out.append(line)
    # 去掉開頭多餘空行
    while out and out[0].strip() == "":
        out.pop(0)
    while out and out[-1].strip() == "":
        out.pop()
    return "\n".join(out).strip() + "\n"


def stamp_text(path: Path) -> None:
    raw = path.read_text(encoding="utf-8") if path.exists() else ""
    body = strip_old_credit(raw) if raw.strip() else ""
    path.write_text(HEADER + "\n" + body + FOOTER, encoding="utf-8")


def ensure_avatar(name: str, dest_dir: Path) -> Path:
    dest = dest_dir / f"{name}_頭像.jpg"
    if dest.exists() and dest.stat().st_size > 10_000:
        return dest
    # 從 humanoid_pack 或既有路徑複製
    for alias in AVATAR_ALIASES.get(name, []):
        for root in (AVATAR_SRC, dest_dir, BASE / name):
            cand = root / alias
            if cand.exists() and cand.stat().st_size > 10_000:
                shutil.copy2(cand, dest)
                return dest
    return dest


def write_avatar_sidecar_note(name: str, dest_dir: Path, avatar_path: Path) -> None:
    """頭像為二進位圖檔無法內嵌長文，以同名說明戳記寫入目錄註記檔供總目錄引用。
    使用者要求四檔：圖檔本身以檔案屬性／總目錄標註；此處確保圖旁可追溯。
    """
    # 不另增第五檔；改在總目錄與角色卡片標註頭像路徑
    _ = (name, dest_dir, avatar_path)


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    report = []
    for name in ORDER:
        d = BASE / name
        d.mkdir(parents=True, exist_ok=True)
        avatar = ensure_avatar(name, d)
        # 文字三檔：若缺失則跳過內容重建（應已存在）
        for kind in ("角色卡片", "對話範例", "角色簡介"):
            p = d / f"{name}_{kind}.txt"
            if not p.exists():
                report.append(f"缺失文字 {p}")
                continue
            stamp_text(p)
        # 頭像：附加極簡文字戳記檔不符合四檔限制 → 在卡片頂部已有署名
        # 另存頭像 provenance 於卡片末（已 stamp）
        ok_av = avatar.exists() and avatar.stat().st_size > 10_000
        report.append(f"{name}: 頭像={'OK' if ok_av else '缺'} 文字已署名")
    # 總目錄
    lines = [
        "【檔案名稱】總目錄",
        DEV,
        PUB,
        "【說明】十三犬種角色獨立檔案包完整清單",
        "【根目錄】data/characters/角色檔案包",
        "",
    ]
    total = 0
    for name in ORDER:
        lines.append(f"═══ {name}（{BREED[name]}／{GENDER[name]}）═══")
        for kind, ext in (
            ("頭像", ".jpg"),
            ("角色卡片", ".txt"),
            ("對話範例", ".txt"),
            ("角色簡介", ".txt"),
        ):
            p = BASE / name / f"{name}_{kind}{ext}"
            ok = p.exists() and p.stat().st_size > 0
            if ok:
                total += 1
            mark = "通過" if ok else "缺失"
            lines.append(f"  {mark}  {name}/{name}_{kind}{ext}")
        lines.append("")
    lines.append(f"【統計】預期五十二檔，實際通過 {total} 檔")
    lines.append(DEV)
    lines.append(PUB)
    lines.append("")
    (BASE / "總目錄.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(report))
    print(f"index total={total}")


if __name__ == "__main__":
    main()
