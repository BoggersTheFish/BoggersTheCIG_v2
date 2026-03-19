"""
Emergence — Detects stabilized clusters and auto-creates new .md files.
Adds emergent nodes to the kernel immediately.
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .ts_kernel import TSKernel, TSNode

VAULT_PATH = "obsidian/TS-Knowledge-Vault"
EMERGENT_PREFIX = "Emergent_Concept_"


def _get_timestamp() -> str:
    """Compact timestamp for emergent node names."""
    return time.strftime("%Y%m%d_%H%M%S", time.gmtime())


def _detect_clusters(kernel: TSKernel) -> List[Set[str]]:
    """
    Detect clusters: nodes connected by edges (weight >= 0.25).
    Simple union-find over edges.
    """
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        pa, pb = find(a), find(b)
        if pa != pb:
            parent[pa] = pb

    for src, dst, w in kernel.edges:
        if w >= 0.25:
            union(src, dst)

    # Group by root
    groups: Dict[str, Set[str]] = {}
    for nid in kernel.nodes:
        r = find(nid)
        groups.setdefault(r, set()).add(nid)

    return [g for g in groups.values() if len(g) >= 2]


def _create_emergent_md(
    vault_path: Path,
    node_id: str,
    summary: str,
    source_nodes: List[str],
    strength: float = 0.6,
) -> Path:
    """Create new .md file with proper frontmatter and summary."""
    vault_path.mkdir(parents=True, exist_ok=True)
    fp = vault_path / f"{node_id}.md"
    tags = source_nodes[:5]
    frontmatter = f"""---
strength: {strength}
tags: [{", ".join(repr(t) for t in tags)}]
---

# {node_id}

{summary}
"""
    fp.write_text(frontmatter, encoding="utf-8")
    return fp


def run_emergence(kernel: TSKernel, vault_path: str = VAULT_PATH) -> List[str]:
    """
    Detect stabilized clusters, create emergent .md files, add nodes to kernel.
    Returns list of created node IDs.
    """
    created: List[str] = []
    vp = Path(vault_path)
    clusters = _detect_clusters(kernel)

    for cluster in clusters:
        node_ids = list(cluster)
        ts = _get_timestamp()
        emergent_id = f"{EMERGENT_PREFIX}{ts}_{len(created)}"
        summary = f"Emergent concept from: {', '.join(node_ids[:5])}"
        _create_emergent_md(vp, emergent_id, summary, node_ids)
        kernel.add_node(emergent_id, base_strength=0.6, tags=node_ids)
        # Add lightweight edges to cluster members
        for nid in node_ids[:5]:
            kernel.edges.append((emergent_id, nid, 0.3))
            kernel.edges.append((nid, emergent_id, 0.3))
        created.append(emergent_id)

    return created
