"""
Ingestor — Raw text / pasted note → extracts key concepts → creates .md with frontmatter.
Called manually or auto-run on every cycle via inbox.md.
"""

import re
import time
from pathlib import Path
from typing import List, Optional, Tuple

VAULT_PATH = "obsidian/TS-Knowledge-Vault"
INBOX_FILE = "inbox.md"
DEFAULT_STRENGTH = 0.5


def _extract_concepts(text: str) -> List[str]:
    """Extract key concepts: wikilinks [[X]], Title_Case phrases, significant words."""
    concepts: List[str] = []
    # Wikilinks [[Concept_Name]]
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", text):
        concepts.append(m.group(1).strip().replace(" ", "_"))
    # Title Case phrases (2+ words)
    for m in re.finditer(r"\b([A-Z][a-z]+(?:_[A-Z][a-z]+)*)\b", text):
        concepts.append(m.group(1))
    # Standalone capitalized words that look like concepts
    for m in re.finditer(r"\b([A-Z][a-zA-Z0-9_]{2,})\b", text):
        c = m.group(1)
        if c not in concepts and c.lower() not in ("the", "and", "for", "but", "not", "you", "all", "can", "are", "was", "has", "had", "its"):
            concepts.append(c)
    # Dedupe, preserve order
    seen = set()
    out = []
    for c in concepts:
        k = c.replace(" ", "_")
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out[:15]  # Cap at 15 tags


def _sanitize_filename(s: str) -> str:
    """Safe filename from concept or summary."""
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s).strip("_")
    return s[:50] if s else "Note"


def process_raw_text(
    raw_text: str,
    vault_path: Path,
    strength: float = DEFAULT_STRENGTH,
    node_type: str = "note",
) -> Tuple[str, Path]:
    """
    Extract concepts from raw text, create .md file with frontmatter.
    Returns (node_id, path_to_created_file).
    """
    concepts = _extract_concepts(raw_text)
    summary = raw_text[:300].strip()
    if len(raw_text) > 300:
        summary += "..."
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    base_name = concepts[0] if concepts else _sanitize_filename(summary[:30])
    node_id = f"{base_name}_{ts}"
    node_id = re.sub(r"[^\w\-]", "_", node_id)

    vault_path.mkdir(parents=True, exist_ok=True)
    fp = vault_path / f"{node_id}.md"
    tags_str = ", ".join(repr(c) for c in concepts[:10])
    content = f"""---
strength: {strength}
tags: [{tags_str}]
type: {node_type}
---

# {node_id}

{summary}
"""
    fp.write_text(content, encoding="utf-8")
    return node_id, fp


def process_inbox(vault_path: str = VAULT_PATH) -> List[str]:
    """
    Process inbox.md: read raw content, create .md files, clear inbox.
    Returns list of created node IDs.
    """
    vp = Path(vault_path)
    inbox = vp / INBOX_FILE
    created: List[str] = []

    if not inbox.exists():
        inbox.parent.mkdir(parents=True, exist_ok=True)
        inbox.write_text("---\n# Inbox\n---\n\nPaste raw notes here. CIG will extract concepts and create nodes.\n", encoding="utf-8")
        return created

    text = inbox.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^---\s*\n.*?\n---\s*\n(.*)", text, re.DOTALL)
    body = match.group(1).strip() if match else text.strip()

    # Skip if empty or just placeholder
    if not body or len(body) < 10 or "Paste raw notes here" in body:
        return created

    node_id, _ = process_raw_text(body, vp)
    created.append(node_id)

    # Clear inbox body, keep frontmatter
    inbox.write_text("---\n# Inbox\n---\n\n", encoding="utf-8")

    return created
