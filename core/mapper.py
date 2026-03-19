"""
Mapper — Smart edge creation: wikilinks [[ ]], keyword overlap, strength-weighted connections.
Replaces tag-only mapping for meaningful edges from day 1.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .ts_kernel import TSKernel

VAULT_PATH = "obsidian/TS-Knowledge-Vault"


class Mapper:
    """Builds edges from wikilinks, keyword overlap, strength-weighted connections."""

    def __init__(self, vault_path: str = VAULT_PATH):
        self.vault_path = Path(vault_path)

    def _extract_wikilinks(self, content: str) -> Set[str]:
        """Extract [[Link]] targets, normalized to node_id style."""
        links = set()
        for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", content):
            links.add(m.group(1).strip().replace(" ", "_"))
        return links

    def _extract_keywords(self, content: str) -> Set[str]:
        """Extract significant words (alphanumeric, 3+ chars) for overlap."""
        words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", content))
        stop = {
            "the", "and", "for", "but", "not", "you", "all", "can", "are", "was",
            "has", "had", "its", "this", "that", "with", "from",
        }
        return words - stop

    def build_edges(self, kernel: TSKernel) -> None:
        """
        Smart mapping: wikilinks, keyword overlap, strength-weighted edges.
        Sets kernel.edges in place.
        """
        edges: List[Tuple[str, str, float]] = []
        node_ids = set(kernel.nodes.keys())

        wikilinks: Dict[str, Set[str]] = {}
        keywords: Dict[str, Set[str]] = {}

        for nid in node_ids:
            wikilinks[nid] = set()
            keywords[nid] = set(kernel.nodes[nid].attributes.get("tags", []))
            fp = self.vault_path / f"{nid}.md"
            if fp.exists():
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                    wikilinks[nid] = self._extract_wikilinks(text)
                    keywords[nid].update(self._extract_keywords(text))
                except Exception:
                    pass

        # 1. Wikilink edges (strong: explicit reference)
        for src, links in wikilinks.items():
            for dst in links:
                if dst in node_ids and src != dst:
                    edges.append((src, dst, 0.7))

        # 2. Keyword overlap (Jaccard)
        nids = list(node_ids)
        for i, a in enumerate(nids):
            for b in nids[i + 1 :]:
                if any((e[0], e[1]) in ((a, b), (b, a)) for e in edges):
                    continue
                ka, kb = keywords.get(a, set()), keywords.get(b, set())
                if not ka or not kb:
                    continue
                overlap = len(ka & kb) / len(ka | kb)
                if overlap > 0.1:
                    edges.append((a, b, min(0.6, overlap + 0.2)))

        # 3. Strength-weighted: connect similar-strength nodes
        strengths = {nid: kernel.nodes[nid].base_strength for nid in node_ids}
        for i, a in enumerate(nids):
            for b in nids[i + 1 :]:
                if any((e[0], e[1]) in ((a, b), (b, a)) for e in edges):
                    continue
                sa, sb = strengths[a], strengths[b]
                diff = abs(sa - sb)
                if diff < 0.2:
                    w = 0.25 + (0.4 - diff) * 0.5
                    edges.append((a, b, min(0.5, w)))

        # Dedupe: keep max weight per (a,b)
        by_pair: Dict[Tuple[str, str], float] = {}
        for a, b, w in edges:
            key = (min(a, b), max(a, b))
            by_pair[key] = max(by_pair.get(key, 0), w)

        kernel.edges = [(a, b, w) for (a, b), w in by_pair.items()]
