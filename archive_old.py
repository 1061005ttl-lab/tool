#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「同一工具的舊版本」自動移到 archive/，只保留最大版號。

用法（放在 repo 根目錄，也就是 .html 檔案同一層）：
    python archive_old.py            # 只預覽，不動檔案
    python archive_old.py --apply    # 實際移動

規則：
- 只處理根目錄、檔名結尾為 _V數字.html（V 大小寫皆可）的檔案
- 同一工具名稱只保留最大版號，其餘移入 archive/
- archive/ 已有同名檔時跳過，不覆蓋
- 在 git repo 內用 git mv（保留歷史），否則用一般搬移
"""
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

APPLY = "--apply" in sys.argv
ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "archive"
PATTERN = re.compile(r"^(.+?)[_ ]?[vV](\d+)\.html$")


def in_git_repo() -> bool:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=ROOT, capture_output=True, text=True,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except FileNotFoundError:
        return False


def main() -> int:
    groups = defaultdict(list)
    for f in ROOT.glob("*.html"):
        m = PATTERN.match(f.name)
        if m:
            groups[m.group(1)].append((int(m.group(2)), f))

    use_git = in_git_repo()
    moved = skipped = 0

    for name in sorted(groups):
        items = sorted(groups[name], key=lambda x: x[0])
        keep = items[-1][1]
        for _, f in items[:-1]:
            dest = ARCHIVE / f.name
            if dest.exists():
                print(f"[跳過] archive 已有同名檔：{f.name}")
                skipped += 1
                continue
            print(f"[{'封存' if APPLY else '預覽'}] {f.name}  （保留 {keep.name}）")
            moved += 1
            if APPLY:
                ARCHIVE.mkdir(exist_ok=True)
                if use_git:
                    subprocess.run(
                        ["git", "mv", str(f), str(dest)], cwd=ROOT, check=True
                    )
                else:
                    shutil.move(str(f), str(dest))

    print(f"\n共 {'已移動' if APPLY else '將移動'} {moved} 個檔案，跳過 {skipped} 個。")
    if not APPLY and moved:
        print("確認無誤後，執行：python archive_old.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
