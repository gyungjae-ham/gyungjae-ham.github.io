#!/usr/bin/env python3
"""Obsidian vault 노트를 AstroPaper 포스트로 변환.

사용 예:
    python3 scripts/from_vault.py "9️⃣ 학습/Batch/_Batch.md"
    python3 scripts/from_vault.py --title "Spring Batch 핵심" --tags "batch,kotlin" \\
        --no-draft "9️⃣ 학습/Batch/01. 배치 처리는 어떤 문제를 해결하는가.md"

vault 경로는 OBSIDIAN_VAULT_PATH 환경 변수 또는 default 값을 사용한다.
인수는 vault root 기준 상대 경로 또는 절대 경로 모두 허용한다.

표준 라이브러리만 사용 (PyYAML 미사용).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_VAULT = (
    "/Users/luca/Library/CloudStorage/GoogleDrive-hiyee0619@gmail.com/My Drive/obsidian"
)
KST = timezone(timedelta(hours=9))

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "src" / "content" / "posts"
ASSETS_BASE = REPO_ROOT / "public" / "assets" / "posts"

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
EMBED_RE = re.compile(r"!\[\[([^\]]+)\]\]")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
FOOTER_RE = re.compile(r"\n+---\s*\n←\s*\[\[[^\]]+\]\]\s*\n*$", re.MULTILINE)
NUMBER_PREFIX_RE = re.compile(r"^\d{2}\.\s*")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """간이 frontmatter 파서. key: value / key: [a, b] 만 지원."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict = {}
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            items = [it.strip().strip("\"'") for it in inner.split(",") if it.strip()]
            meta[key] = items
        else:
            meta[key] = value.strip("\"'")
    return meta, body


def find_vault_note(arg: str, vault_root: Path) -> Path:
    p = Path(arg)
    if p.is_absolute() and p.exists():
        return p
    candidate = vault_root / arg
    if candidate.exists():
        return candidate
    if not arg.endswith(".md"):
        c2 = vault_root / (arg + ".md")
        if c2.exists():
            return c2
    raise FileNotFoundError(f"vault에서 노트를 찾을 수 없습니다: {arg}")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w가-힣\-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "post"


def transform_body(
    body: str, slug: str, vault_root: Path, source_dir: Path
) -> str:
    body = FOOTER_RE.sub("", body).rstrip() + "\n"

    asset_dir = ASSETS_BASE / slug
    web_prefix = f"/assets/posts/{slug}"

    def copy_asset(src: Path, fname: str) -> str:
        asset_dir.mkdir(parents=True, exist_ok=True)
        dest = asset_dir / fname
        if not dest.exists():
            shutil.copy2(src, dest)
        return f"{web_prefix}/{fname}"

    def embed_replace(m: "re.Match[str]") -> str:
        raw = m.group(1).strip()
        fname = Path(raw).name
        for cand in vault_root.rglob(fname):
            web = copy_asset(cand, fname)
            return f"![{fname}]({web})"
        return f"_(missing image: {raw})_"

    def md_image_replace(m: "re.Match[str]") -> str:
        alt, src = m.group(1), m.group(2)
        if src.startswith(("http://", "https://", "/", "data:")):
            return m.group(0)
        for base in (source_dir, vault_root):
            cand = (base / src).resolve()
            if cand.exists():
                web = copy_asset(cand, cand.name)
                return f"![{alt}]({web})"
        return m.group(0)

    def wikilink_replace(m: "re.Match[str]") -> str:
        target, alias = m.group(1).strip(), m.group(2)
        label = alias.strip() if alias else target
        return f"**{label}**"

    body = EMBED_RE.sub(embed_replace, body)
    body = MD_IMAGE_RE.sub(md_image_replace, body)
    body = WIKILINK_RE.sub(wikilink_replace, body)
    return body


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{label}{suffix}: ").strip()
    except EOFError:
        return default
    return val or default


def prompt_bool(label: str, default: bool) -> bool:
    d = "Y/n" if default else "y/N"
    try:
        val = input(f"{label} ({d}): ").strip().lower()
    except EOFError:
        return default
    if not val:
        return default
    return val in ("y", "yes", "true", "1")


def format_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            inner = ", ".join(f'"{x}"' for x in v)
            lines.append(f"{k}: [{inner}]")
        elif isinstance(v, datetime):
            lines.append(f"{k}: {v.isoformat()}")
        else:
            s = str(v).replace('"', '\\"')
            lines.append(f'{k}: "{s}"')
    lines.append("---")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Vault 노트 → AstroPaper 포스트 변환")
    p.add_argument("note", help="vault 내 노트 경로 (상대/절대)")
    p.add_argument("--title")
    p.add_argument("--description")
    p.add_argument("--tags", help="콤마 구분")
    p.add_argument("--slug")
    p.add_argument("--featured", action="store_true")
    p.add_argument("--no-draft", action="store_true", help="Draft 아님 (즉시 공개 의도)")
    p.add_argument("--force", action="store_true", help="존재 시 덮어쓰기")
    p.add_argument(
        "--vault",
        default=os.environ.get("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT),
    )
    args = p.parse_args()

    vault_root = Path(args.vault).expanduser().resolve()
    if not vault_root.exists():
        print(f"vault 경로 없음: {vault_root}", file=sys.stderr)
        return 1

    note_path = find_vault_note(args.note, vault_root)
    text = note_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    default_title = NUMBER_PREFIX_RE.sub("", note_path.stem)
    title = args.title or prompt("제목", default_title)

    slug = args.slug or prompt("slug (영문 권장)", slugify(title))

    first_para = ""
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("```"):
            first_para = s
            break
    default_desc = (
        (first_para[:120] + ("…" if len(first_para) > 120 else "")) if first_para else ""
    )
    description = args.description or prompt("한 줄 설명", default_desc)
    if not description:
        print("description은 필수입니다 (AstroPaper schema).", file=sys.stderr)
        return 1

    vault_tags = fm.get("tags", [])
    if isinstance(vault_tags, str):
        vault_tags = [t.strip() for t in vault_tags.split(",") if t.strip()]
    default_tags = ", ".join(vault_tags) if vault_tags else "기타"
    if args.tags is not None:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    else:
        raw = prompt("태그 (콤마)", default_tags)
        tags = [t.strip() for t in raw.split(",") if t.strip()]

    featured = args.featured or prompt_bool("featured?", False)
    draft = False if args.no_draft else prompt_bool("draft (검토 후 공개)?", True)

    pub = datetime.now(KST).replace(microsecond=0)
    meta = {
        "author": "luca",
        "pubDatetime": pub,
        "title": title,
        "featured": featured,
        "draft": draft,
        "tags": tags,
        "description": description,
    }

    out_path = POSTS_DIR / f"{slug}.md"
    if out_path.exists() and not args.force:
        if not prompt_bool(f"이미 존재함: {out_path.name}. 덮어쓸까요?", False):
            print("취소.")
            return 1

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    transformed = transform_body(body, slug, vault_root, note_path.parent)
    out_path.write_text(
        format_frontmatter(meta) + "\n\n" + transformed.lstrip("\n"),
        encoding="utf-8",
    )

    print(f"\n✅ 저장: {out_path.relative_to(REPO_ROOT)}")
    print(f"   draft={draft}  featured={featured}  tags={tags}")
    print("\n다음 단계:")
    print("  1) 미리보기:  npm run dev   → http://localhost:4321")
    print("  2) 본문 검토 후 수정")
    if draft:
        print("  3) 공개 시:   frontmatter draft 를 false 로 바꾸고 commit/push")
    else:
        print("  3) 즉시 공개: git add . && git commit -m '...' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
