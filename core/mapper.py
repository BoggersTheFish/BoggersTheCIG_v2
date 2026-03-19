"""
Mapper — Smart edge creation: wikilinks [[ ]], keyword overlap, strength-weighted connections.
Replaces tag-only mapping for meaningful edges from day 1.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

from .ts_kernel import TSKernel

VAULT_PATH = "obsidian/TS-Knowledge-Vault"


def _extract_wikilinks(content: str) -> Set[str]:
    """Extract [[Link]] targets, normalized to node_id style."""
    links = set()
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", content):
        links.add(m.group(1).strip().replace(" ", "_"))
    return links


def _extract_keywords(content: str) -> Set[str]:
    """Extract significant words (alphanumeric, 3+ chars) for overlap."""
    words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", content))
    stop = {"the", "and", "for", "but", "not", "you", "all", "can", "are", "was", "has", "had", "its", "this", "that", "with", "from"}
    return words - stop


def build_edges(kernel: TSKernel, vault_path: str = VAULT_PATH) -> List[Tuple[str, str, float]]:
    """
    Build edges from: wikilinks, keyword overlap, strength-weighted connections.
    Returns list of (src, dst, weight). Caller sets kernel.edges = result.
    """
    vp = Path(vault_path)
    edges: List[Tuple[str, str, float]] = []
    node_ids = set(kernel.nodes.keys())

    # Per-node: wikilinks and keywords
    wikilinks: Dict[str, Set[str]] = {}
    keywords: Dict[str, Set[str]] = {}

    for nid in node_ids:
        wikilinks[nid] = set()
        keywords[nid] = set(kernel.nodes[nid].attributes.get("tags", []))
        fp = vp / f"{nid}.md"
        if fp.exists():
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
                wikilinks[nid] = _extract_wikilinks(text)
                keywords[nid].update(_extract_keywords(text))
            except Exception:
                pass

    # 1. Wikilink edges (strong: explicit reference)
    for src, links in wikilinks.items():
        for dst in links:
            if dst in node_ids and src != dst:
                w = 0.7  # Strong explicit link
                edges.append((src, dst, w))

    # 2. Keyword overlap (Jaccard)
    nids = list(node_ids)
    for i, a in enumerate(nids):
        for b in nids[i + 1 :]:
            if (a, b) in [(e[0], e[1]) for e in edges] or (b, a) in [(e[0], e[1]) for e in edges]:
                continue  # Already have wikilink
            ka, kb = keywords.get(a, set()), keywords.get(b, set())
            if not ka or not kb:
                continue
            overlap = len(ka & kb) / len(ka | kb)
            if overlap > 0.1:
                edges.append((a, b, min(0.6, overlap + 0.2)))

    # 3. Strength-weighted: connect high-strength nodes to similar-strength
    strengths = {nid: kernel.nodes[nid].base_strength for nid in node_ids}
    for i, a in enumerate(nids):
        for b in nids[i + 1 :]:
            if any(e[0] == a and e[1] == b or e[0] == b and e[1] == a for e in edges):
                continue
            sa, sb = strengths[a], strengths[b]
            diff = abs(sa - sb)
            if diff < 0.2:  # Similar strength
                w = 0.25 + (0.4 - diff) * 0.5
                edges.append((a, b, min(0.5, w)))

    # Dedupe: keep max weight per (a,b)
    by_pair: Dict[Tuple[str, str], float] = {}
    for a, b, w in edges:
        key = (min(a, b), max(a, b))
        by_pair[key] = max(by_pair.get(key, 0), w)

    return [(a, b, w) for (a, b), w in by_pair.items()]
