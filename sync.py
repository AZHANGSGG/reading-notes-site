#!/usr/bin/env python3
"""
sync.py — 把 Obsidian 读书笔记 + pptx 课件同步到 VitePress 站点

用法：
    python3 sync.py                          # 同步笔记 + 课件
    python3 sync.py --no-slides              # 跳过 pptx 课件转换（更快）
    python3 sync.py --rebuild-slides         # 强制重建所有课件（不用缓存）
    python3 sync.py --vault /path/to/vault   # 指定其他 vault
    python3 sync.py --dry-run                # 只看会做什么

流程：
1. 扫描 vault「读书笔记/」下每本书的子目录
2. 复制 .md 笔记到 docs/books/<书名>/
3. 把书目录里的 .pptx 转成图片（libreoffice → pdf → pdftoppm → jpeg）
4. 生成每本书的 index.md（书首页）和 99_课件.md（课件画廊）
5. 重建 docs/books/index.md（卡片网格的书架）
6. 重建 docs/index.md（站点首页）
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_VAULT = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "iCloud~md~obsidian"
    / "Documents"
    / "My Vault"
    / "读书笔记"
)
PROJECT_ROOT = Path(__file__).resolve().parent
DOCS_DIR = PROJECT_ROOT / "docs"
BOOKS_DIR = DOCS_DIR / "books"
SLIDES_CACHE = PROJECT_ROOT / ".slides_cache"

EXCLUDE_FILES = {".DS_Store"}

# ── 公开化过滤规则 ────────────────────────────────────────────────
# 内部代号 / 客户名等敏感词不写进公开仓库，统一放在 gitignored 的本地文件
# sanitize_rules.local.json 里。文件缺失时直接报错退出，避免在“没有过滤”的
# 情况下把内部内容同步成公开内容。
SANITIZE_RULES_FILE = PROJECT_ROOT / "sanitize_rules.local.json"


def _load_sanitize_rules() -> dict:
    if not SANITIZE_RULES_FILE.exists():
        sys.exit(
            f"\n❌ 找不到脱敏规则文件：{SANITIZE_RULES_FILE}\n"
            "   它含内部敏感词，刻意不进版本库（见 .gitignore）。\n"
            "   请按下面格式创建后再运行 sync.py：\n"
            "   {\n"
            '     "exclude_file_patterns": ["…"],\n'
            '     "section_title_blacklist": ["…"],\n'
            '     "paragraph_blacklist": ["…"]\n'
            "   }\n"
        )
    try:
        return json.loads(SANITIZE_RULES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"\n❌ 脱敏规则文件 JSON 解析失败：{e}\n")


def _compile_rules(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_SANITIZE = _load_sanitize_rules()

# 文件名命中 → 整个文件跳过。“逐字稿”是通用规则、非敏感，保留在代码里。
EXCLUDE_PATTERNS = [re.compile(r"逐字稿")] + _compile_rules(
    _SANITIZE.get("exclude_file_patterns", [])
)
INDEX_PATTERNS = [
    re.compile(r"^00[_-]"),
    re.compile(r"^全书索引"),
    re.compile(r"^README", re.IGNORECASE),
]

# 标题命中 → 整个小节剥离；段落命中 → 整段剥离。敏感词见 sanitize_rules.local.json。
SECTION_TITLE_BLACKLIST = _compile_rules(_SANITIZE.get("section_title_blacklist", []))
PARAGRAPH_BLACKLIST = _compile_rules(_SANITIZE.get("paragraph_blacklist", []))
ICONS = ["📘", "📗", "📕", "📙", "📔", "📓", "📒", "📚", "📖"]

SOFFICE_FALLBACK = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


# === 工具函数 ===

def should_exclude(name: str) -> bool:
    if name in EXCLUDE_FILES:
        return True
    return any(p.search(name) for p in EXCLUDE_PATTERNS)


def collect_md_files(book_dir: Path) -> list[Path]:
    files = [p for p in book_dir.rglob("*.md") if not should_exclude(p.name)]
    files.sort(key=lambda x: x.name)
    return files


def collect_pptx(book_dir: Path) -> Path | None:
    pptxs = sorted(
        (p for p in book_dir.rglob("*.pptx") if not should_exclude(p.name)),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return pptxs[0] if pptxs else None


def first_h1(md: str) -> str | None:
    m = re.search(r"^#\s+(.+?)\s*$", md, re.MULTILINE)
    return m.group(1).strip() if m else None


def parse_frontmatter(md: str) -> dict:
    out = {}
    if not md.startswith("---"):
        return out
    end = md.find("\n---", 3)
    if end < 0:
        return out
    for line in md[3:end].strip().splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def sanitize_for_public(md: str) -> str:
    """剥离不适合公开的内容：黑名单标题对应的整段、含敏感关键词的段落、frontmatter 中含敏感词的行。"""
    # 1. 切出 frontmatter，并对其做行级过滤（删除含敏感词的整行，例如 tags 里的私密标签）
    frontmatter = ""
    body = md
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end > 0:
            fm_raw = md[: end + 4]
            body = md[end + 4 :].lstrip("\n")
            fm_lines = [
                line for line in fm_raw.split("\n")
                if not any(pat.search(line) for pat in PARAGRAPH_BLACKLIST)
            ]
            frontmatter = "\n".join(fm_lines)

    # 2. 删除黑名单标题对应的整个小节
    lines = body.split("\n")
    kept: list[str] = []
    skip_until_level: int | None = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2)
            if skip_until_level is not None and level <= skip_until_level:
                skip_until_level = None
            if skip_until_level is None and any(p.search(title) for p in SECTION_TITLE_BLACKLIST):
                skip_until_level = level
                continue
            if skip_until_level is not None:
                continue
            kept.append(line)
        elif skip_until_level is not None:
            continue
        else:
            kept.append(line)
    body = "\n".join(kept)

    # 3. 按段落过滤（段落 = 空行分隔的连续行块）
    paragraphs = re.split(r"\n\s*\n", body)
    paragraphs = [p for p in paragraphs if not any(pat.search(p) for pat in PARAGRAPH_BLACKLIST)]
    body = "\n\n".join(paragraphs)

    # 4. 删除空小节（标题后立即跟另一个同级/更高级标题，中间无实质内容）
    for _ in range(5):  # 反复扫，处理嵌套
        new_body = _strip_empty_sections(body)
        if new_body == body:
            break
        body = new_body

    # 5. 收拢多余空行
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if body:
        body += "\n"

    return (frontmatter + "\n" + body) if frontmatter else body


def _strip_empty_sections(md: str) -> str:
    """删除标题后没有内容的小节（标题直接跟另一个同级/更高级标题或文件末尾）。"""
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(#{1,6})\s+", line)
        if m:
            level = len(m.group(1))
            has_content = False
            j = i + 1
            while j < len(lines):
                l2 = lines[j]
                m2 = re.match(r"^(#{1,6})\s+", l2)
                if m2:
                    if len(m2.group(1)) <= level:
                        break  # 同级或更高级标题 → 当前小节结束
                    has_content = True  # 子标题算内容
                    break
                stripped = l2.strip()
                if stripped and stripped != "---":
                    has_content = True
                    break
                j += 1
            if not has_content:
                i += 1
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def title_for(file_path: Path) -> str:
    try:
        title = first_h1(file_path.read_text(encoding="utf-8"))
        # H1 含敏感词时回退到文件名（不能把内部代号带到公开章节列表）
        if title and not any(pat.search(title) for pat in PARAGRAPH_BLACKLIST):
            return title
    except Exception:
        pass
    name = re.sub(r"^[0-9]+[_-]", "", file_path.stem)
    return name.replace("_", " ")


def is_index_file(name: str) -> bool:
    return any(p.search(name) for p in INDEX_PATTERNS)


def get_book_metadata(book_src: Path) -> dict:
    files = collect_md_files(book_src)
    chapter_files = [f for f in files if not is_index_file(f.name)]

    author = ""
    index_file = next((f for f in files if is_index_file(f.name)), None)
    # 优先从索引文件读 author，没有就回退到任意章节文件
    candidates = [index_file] + [f for f in files if f is not index_file]
    for cand in candidates:
        if cand is None:
            continue
        try:
            fm = parse_frontmatter(cand.read_text(encoding="utf-8"))
            if fm.get("author"):
                author = fm["author"]
                break
        except Exception:
            pass

    return {
        "name": book_src.name,
        "author": author,
        "note_count": len(chapter_files),
        "files": files,
        "chapter_files": chapter_files,
        "index_file": index_file,
        "pptx": collect_pptx(book_src),
        "src": book_src,
        "has_slides": False,
        "slide_count": 0,
    }


# === 课件转换 ===

def soffice_path() -> str | None:
    p = shutil.which("soffice")
    if p:
        return p
    if Path(SOFFICE_FALLBACK).exists():
        return SOFFICE_FALLBACK
    return None


def check_slides_tools() -> bool:
    if not soffice_path():
        print("⚠️  没找到 LibreOffice。装一下：brew install --cask libreoffice")
        return False
    if not shutil.which("pdftoppm"):
        print("⚠️  没找到 pdftoppm。装一下：brew install poppler")
        return False
    return True


def convert_pptx_to_images(pptx: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_dir.parent / f".{out_dir.name}_tmp"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [soffice_path(), "--headless", "--convert-to", "pdf",
         "--outdir", str(tmp_dir), str(pptx)],
        check=True, capture_output=True,
    )

    pdfs = list(tmp_dir.glob("*.pdf"))
    if not pdfs:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f"LibreOffice 没生成 PDF: {pptx}")
    pdf = pdfs[0]

    subprocess.run(
        ["pdftoppm", "-jpeg", "-jpegopt", "quality=85", "-r", "110",
         str(pdf), str(out_dir / "slide")],
        check=True, capture_output=True,
    )

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return sorted(out_dir.glob("slide-*.jpg"))


def get_or_build_slides(book: str, pptx: Path) -> list[Path] | None:
    cache_dir = SLIDES_CACHE / book
    mtime_file = cache_dir / ".pptx_mtime"
    src_mtime = str(int(pptx.stat().st_mtime))

    cached_imgs = sorted(cache_dir.glob("slide-*.jpg")) if cache_dir.exists() else []
    cached_mtime = mtime_file.read_text().strip() if mtime_file.exists() else ""

    if cached_imgs and cached_mtime == src_mtime:
        return cached_imgs

    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"     ⚙️  转换 pptx → 图片（首次约 30 秒）...")
    try:
        images = convert_pptx_to_images(pptx, cache_dir)
    except Exception as e:
        print(f"     ❌ pptx 转换失败: {e}")
        return None

    mtime_file.write_text(src_mtime)
    return images


def install_slides(book_meta: dict, target_book_dir: Path) -> int:
    images = get_or_build_slides(book_meta["name"], book_meta["pptx"])
    if not images:
        return 0

    slides_dir = target_book_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    for img in images:
        shutil.copy2(img, slides_dir / img.name)

    lines = [
        "# 课件",
        "",
        f"> {book_meta['author']}" if book_meta["author"] else "",
        "",
        f"基于本书内容制作的讲课课件，共 {len(images)} 页。点击任意一页可放大查看。",
        "",
        '<div class="slides-grid">',
        "",
    ]
    for i, img in enumerate(images, start=1):
        lines.append(
            f'<figure><img src="./slides/{img.name}" alt="第 {i} 页" loading="lazy" />'
            f'<figcaption>{i}</figcaption></figure>'
        )
    lines += ["", "</div>", ""]
    (target_book_dir / "99_课件.md").write_text("\n".join(lines), encoding="utf-8")
    return len(images)


# === 索引页生成 ===

def write_book_index(m: dict, target_book_dir: Path) -> None:
    book = m["name"]
    lines = [f"# {book}", ""]
    if m["author"]:
        lines += [f"> {m['author']}", ""]

    if m["index_file"]:
        try:
            content = m["index_file"].read_text(encoding="utf-8")
            content = sanitize_for_public(content)
            if content.startswith("---"):
                end = content.find("\n---", 3)
                if end > 0:
                    content = content[end + 4:].lstrip()
            content = re.sub(r"^#\s+.+\n", "", content, count=1)
            lines += [content.strip(), ""]
        except Exception:
            pass

    lines += ["## 章节", ""]
    for f in m["chapter_files"]:
        lines.append(f"- [{title_for(f)}](./{f.stem})")

    if m["has_slides"]:
        lines += ["", "## 课件", ""]
        lines.append(f"- [📊 完整课件画廊（{m['slide_count']} 页）](./99_课件)")

    lines.append("")
    (target_book_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_master_index(books_meta: list[dict]) -> None:
    lines = [
        "---",
        "title: 书架",
        "---",
        "",
        "# 书架",
        "",
        "精读过的书，按完成顺序收纳在这里。每本含完整笔记和讲课课件。",
        "",
        '<div class="bookshelf">',
        "",
    ]
    for i, m in enumerate(books_meta):
        icon = ICONS[i % len(ICONS)]
        meta_parts = [f"{m['note_count']} 篇精读"]
        if m["has_slides"]:
            meta_parts.append(f"{m['slide_count']} 页课件")
        meta_html = "".join(f"<span>{p}</span>" for p in meta_parts)
        author = m["author"] or "&nbsp;"
        lines += [
            f'<a class="book-card" href="./{m["name"]}/">',
            f'  <div class="book-title">{icon} {m["name"]}</div>',
            f'  <div class="book-author">{author}</div>',
            f'  <div class="book-meta">{meta_html}</div>',
            '</a>',
            "",
        ]
    lines += ['</div>', ""]
    (BOOKS_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_homepage(books_meta: list[dict]) -> None:
    lines = [
        "---",
        "layout: home",
        "",
        "hero:",
        '  name: "AZ 的读书笔记"',
        '  text: "读过的书 · 留下的痕迹"',
        "  tagline: 把每一本读过的书，沉淀成可以反复回看的知识 — 也作为讲课与对外分享的底稿",
        "  actions:",
        "    - theme: brand",
        "      text: 进入书架 →",
        "      link: /books/",
        "    - theme: alt",
        "      text: 关于这个站点",
        "      link: /about",
        "",
        "features:",
    ]
    for i, m in enumerate(books_meta):
        icon = ICONS[i % len(ICONS)]
        meta_parts = [f"{m['note_count']} 篇精读"]
        if m["has_slides"]:
            meta_parts.append("含课件")
        details = " · ".join(([m["author"]] if m["author"] else []) + meta_parts)
        details_safe = details.replace('\\', '\\\\').replace('"', '\\"')
        lines += [
            f"  - title: {icon} {m['name']}",
            f'    details: "{details_safe}"',
            f"    link: /books/{m['name']}/",
            f"    linkText: 进入",
        ]
    lines += ["---", ""]
    (DOCS_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


# === 主流程 ===

def sync(vault_dir: Path, dry_run=False, do_slides=True, rebuild_slides=False) -> None:
    if not vault_dir.exists():
        print(f"❌ vault 目录不存在: {vault_dir}", file=sys.stderr)
        sys.exit(1)

    # `_`/`.` 前缀的目录是内部用途（如 _工作索引：项目指令/skills/背景资料），
    # 不是书，绝不同步到公开站点。
    book_dirs = [
        c for c in sorted(vault_dir.iterdir())
        if c.is_dir()
        and not c.name.startswith(("_", "."))
        and collect_md_files(c)
    ]
    if not book_dirs:
        print(f"⚠️  在 {vault_dir} 里没找到包含 .md 笔记的书目录")
        return

    print(f"📚 在 {vault_dir} 找到 {len(book_dirs)} 本有笔记的书：")
    for b in book_dirs:
        print(f"   • {b.name}")
    print()

    if dry_run:
        print("(dry-run) 不会真的复制文件")
        return

    books_meta = [get_book_metadata(b) for b in book_dirs]

    can_slides = do_slides and check_slides_tools()
    if rebuild_slides and SLIDES_CACHE.exists():
        print("🗑  清空课件缓存…")
        shutil.rmtree(SLIDES_CACHE)

    if BOOKS_DIR.exists():
        for child in BOOKS_DIR.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.name == "index.md":
                child.unlink()
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)

    total_files = 0
    for m in books_meta:
        target = BOOKS_DIR / m["name"]
        target.mkdir(parents=True, exist_ok=True)
        for f in m["files"]:
            content = f.read_text(encoding="utf-8")
            content = sanitize_for_public(content)
            (target / f.name).write_text(content, encoding="utf-8")
            total_files += 1

        slide_msg = ""
        if can_slides and m["pptx"]:
            n = install_slides(m, target)
            if n:
                m["has_slides"] = True
                m["slide_count"] = n
                slide_msg = f" + {n} 页课件"

        write_book_index(m, target)
        print(f"  ✅ {m['name']}: {m['note_count']} 篇笔记{slide_msg}")

    write_master_index(books_meta)
    write_homepage(books_meta)

    print()
    print(f"🎉 同步完成: {len(books_meta)} 本书 / {total_files} 篇笔记")
    slides_books = sum(1 for m in books_meta if m["has_slides"])
    if slides_books:
        total_slides = sum(m["slide_count"] for m in books_meta)
        print(f"   📊 课件: {slides_books} 本书 / {total_slides} 页")
    print(f"   → 位置: {BOOKS_DIR}")
    print()
    print("下一步：")
    print("  npm run dev   或   git add . && git commit -m '更新' && git push")


def main():
    parser = argparse.ArgumentParser(description="把 Obsidian 读书笔记同步到 VitePress 站点")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-slides", action="store_true", help="跳过 pptx 课件转换")
    parser.add_argument("--rebuild-slides", action="store_true", help="强制重建所有课件")
    args = parser.parse_args()
    sync(args.vault, dry_run=args.dry_run,
         do_slides=not args.no_slides, rebuild_slides=args.rebuild_slides)


if __name__ == "__main__":
    main()
