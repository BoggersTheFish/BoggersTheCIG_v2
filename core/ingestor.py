"""
Ingestor — Raw text / pasted note → extracts key concepts → creates .md with frontmatter.
Class-based API: ingest(raw_text), process_inbox().
"""

import re
import time
from pathlib import Path
from typing import List, Optional

VAULT_PATH = "obsidian/TS-Knowledge-Vault"
INBOX_FILE = "inbox.md"
DEFAULT_STRENGTH = 0.5


class Ingestor:
    """Ingests raw text, extracts concepts, creates clean .md files with frontmatter."""

    def __init__(self, vault_path: str = VAULT_PATH):
        self.vault_path = Path(vault_path)

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts: wikilinks [[X]], Title_Case phrases, significant words."""
        concepts: List[str] = []
        for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", text):
            concepts.append(m.group(1).strip().replace(" ", "_"))
        for m in re.finditer(r"\b([A-Z][a-z]+(?:_[A-Z][a-z]+)*)\b", text):
            concepts.append(m.group(1))
        for m in re.finditer(r"\b([A-Z][a-zA-Z0-9_]{2,})\b", text):
            c = m.group(1)
            if c not in concepts and c.lower() not in (
                "the", "and", "for", "but", "not", "you", "all", "can", "are", "was", "has", "had", "its"
            ):
                concepts.append(c)
        seen = set()
        out = []
        for c in concepts:
            k = c.replace(" ", "_")
            if k and k not in seen:
                seen.add(k)
                out.append(k)
        return out[:15]

    def _sanitize_filename(self, s: str) -> str:
        """Safe filename from concept or summary."""
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_]+", "_", s).strip("_")
        return s[:50] if s else "Note"

    def ingest(self, raw_text: str, strength: float = DEFAULT_STRENGTH) -> str:
        """
        Ingest raw text: extract concepts, create .md file with frontmatter.
        Returns node_id of created file.
        """
        concepts = self._extract_concepts(raw_text)
        summary = raw_text[:300].strip()
        if len(raw_text) > 300:
            summary += "..."
        ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        base_name = concepts[0] if concepts else self._sanitize_filename(summary[:30])
        node_id = f"{base_name}_{ts}"
        node_id = re.sub(r"[^\w\-]", "_", node_id)

        self.vault_path.mkdir(parents=True, exist_ok=True)
        fp = self.vault_path / f"{node_id}.md"
        tags_str = ", ".join(repr(c) for c in concepts[:10])
        content = f"""---
strength: {strength}
tags: [{tags_str}]
type: ingested
---

# {node_id}

{summary}
"""
        fp.write_text(content, encoding="utf-8")
        return node_id

    def process_inbox(self) -> List[str]:
        """
        Process inbox.md if present: read raw content, ingest, clear inbox.
        Returns list of created node IDs.
        """
        inbox = self.vault_path / INBOX_FILE
        created: List[str] = []

        if not inbox.exists():
            self.vault_path.mkdir(parents=True, exist_ok=True)
            inbox.write_text(
                "---\n# Inbox\n---\n\nPaste raw notes here. CIG will extract concepts and create nodes.\n",
                encoding="utf-8",
            )
            return created

        text = inbox.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^---\s*\n.*?\n---\s*\n(.*)", text, re.DOTALL)
        body = match.group(1).strip() if match else text.strip()

        if not body or len(body) < 10 or "Paste raw notes here" in body:
            return created

        node_id = self.ingest(body)
        created.append(node_id)

        inbox.write_text("---\n# Inbox\n---\n\n", encoding="utf-8")
        return created
