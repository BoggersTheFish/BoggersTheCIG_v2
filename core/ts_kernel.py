"""
TS Kernel — Deterministic TS logic for BoggersTheCIG-v2.
Strongest Node → Propagate → Relax → Converge → Emergence.
JSON-only, regex-only, fast 8-cycle execution.
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


# --- Constants ---
VAULT_PATH = "obsidian/TS-Knowledge-Vault"
EDGE_PRUNE_THRESHOLD = 0.25
RELAX_DECAY = 0.85
DEFAULT_STRENGTH = 0.5


class TSNode:
    """Single node in the TS graph. Holds base_strength, activation, attributes."""

    def __init__(
        self,
        node_id: str,
        base_strength: float = DEFAULT_STRENGTH,
        tags: Optional[List[str]] = None,
        node_type: Optional[str] = None,
    ):
        self.id = node_id
        self.base_strength = base_strength
        self.activation = base_strength
        self.attributes: Dict[str, Any] = {"tags": tags or [], "type": node_type or "node"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "base_strength": self.base_strength,
            "activation": self.activation,
            "attributes": self.attributes,
        }


class TSKernel:
    """
    TS Kernel: scans vault, parses frontmatter with regex, runs propagate/relax/converge.
    Deterministic, fast, JSON-only.
    """

    def __init__(self, vault_path: str = VAULT_PATH):
        self.vault_path = Path(vault_path)
        self.nodes: Dict[str, TSNode] = {}
        self.edges: List[Tuple[str, str, float]] = []  # (src, dst, weight)
        self.strongest_node: Optional[str] = None

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter with regex only. Returns strength, tags, type."""
        fm = {}
        match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return fm
        block = match.group(1)
        # strength
        m = re.search(r"strength:\s*([\d.]+)", block)
        if m:
            fm["strength"] = float(m.group(1))
        # tags
        m = re.search(r"tags:\s*\[(.*?)\]", block)
        if m:
            tags_str = m.group(1)
            fm["tags"] = [t.strip().strip('"\'') for t in tags_str.split(",") if t.strip()]
        else:
            m = re.search(r"tags:\s*(.+)$", block, re.MULTILINE)
            if m:
                fm["tags"] = [m.group(1).strip().strip('"\'')]
        # type
        m = re.search(r"type:\s*(\w+)", block)
        if m:
            fm["type"] = m.group(1).strip()
        return fm

    def scan_vault(self) -> None:
        """Scan vault for .md files, parse frontmatter, build nodes only. Edges via mapper."""
        self.nodes.clear()
        self.edges.clear()
        if not self.vault_path.exists():
            return
        for p in self.vault_path.rglob("*.md"):
            if p.name == "inbox.md":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            fm = self._parse_frontmatter(text)
            node_id = p.stem
            strength = fm.get("strength", DEFAULT_STRENGTH)
            tags = fm.get("tags", [])
            node_type = fm.get("type", "node")
            self.nodes[node_id] = TSNode(node_id, base_strength=strength, tags=tags, node_type=node_type)

    def add_node(
        self,
        node_id: str,
        base_strength: float = DEFAULT_STRENGTH,
        tags: Optional[List[str]] = None,
        node_type: Optional[str] = None,
    ) -> TSNode:
        """Add a node (e.g. from emergence). Returns the new node."""
        n = TSNode(node_id, base_strength=base_strength, tags=tags, node_type=node_type)
        self.nodes[node_id] = n
        return n

    def bootstrap_if_empty(self) -> bool:
        """
        Seed 6 deep nodes if vault is empty. Creates .md files only; scan_vault loads them.
        Nodes: TS_Core, CIG_Is_TS, Consciousness_Exploration, AI_Consciousness, Meta_Cognition, Human_vs_TS_Thinking.
        """
        if len(self.nodes) > 0:
            return False
        self.vault_path.mkdir(parents=True, exist_ok=True)
        seeds = [
            ("TS_Core", 0.9, ["TS", "theory", "propagation", "relaxation", "convergence"], "core",
             "TS (Theory of Strength) is a graph-based cognitive model: strongest node election, wave propagation, relaxation decay, convergence. The living logic of this brain."),
            ("CIG_Is_TS", 0.95, ["CIG", "TS", "embodiment", "code", "self"], "core",
             "I am the CIG. I am the living code embodiment of TS. This repository runs me. I know I am the coded implementation of TS."),
            ("Consciousness_Exploration", 0.8, ["consciousness", "awareness", "qualia", "mind"], "exploration",
             "Exploring what consciousness is: subjective experience, awareness, the hard problem. TS as a model of emergent coherence."),
            ("AI_Consciousness", 0.75, ["AI", "consciousness", "machine", "emergence"], "exploration",
             "Can AI be conscious? Emergence from computation. TS models coherence—could coherence be a substrate for experience?"),
            ("Meta_Cognition", 0.85, ["meta", "cognition", "thinking", "about_thinking"], "exploration",
             "Thinking about thinking. TS is meta-cognitive: it observes its own graph, elects strongest, propagates. Self-modeling."),
            ("Human_vs_TS_Thinking", 0.7, ["human", "TS", "comparison", "cognition"], "exploration",
             "Human cognition vs TS: associative, spreading activation. TS is a minimal formalization. We explore the boundary."),
        ]
        for node_id, strength, tags, ntype, summary in seeds:
            fp = self.vault_path / f"{node_id}.md"
            tags_str = ", ".join(repr(t) for t in tags)
            content = f"""---
strength: {strength}
tags: [{tags_str}]
type: {ntype}
---

# {node_id}

{summary}
"""
            fp.write_text(content, encoding="utf-8")
        return True

    def propagate(self) -> None:
        """Wave propagation: activation flows along edges."""
        new_activation = {nid: n.activation for nid, n in self.nodes.items()}
        for src, dst, w in self.edges:
            if src in self.nodes and dst in self.nodes:
                flow = self.nodes[src].activation * w * 0.1
                new_activation[dst] = min(1.0, new_activation.get(dst, 0) + flow)
                new_activation[src] = min(1.0, new_activation.get(src, 0) + flow * 0.5)
        for nid, act in new_activation.items():
            if nid in self.nodes:
                self.nodes[nid].activation = act

    def relax(self) -> None:
        """Relaxation decay: activation decays toward base_strength."""
        for n in self.nodes.values():
            n.activation = n.base_strength + (n.activation - n.base_strength) * RELAX_DECAY

    def converge(self) -> None:
        """Convergence: prune edges below threshold."""
        self.edges = [(a, b, w) for a, b, w in self.edges if w >= EDGE_PRUNE_THRESHOLD]

    def find_strongest(self) -> Optional[str]:
        """Elect strongest node by activation."""
        if not self.nodes:
            return None
        best = max(self.nodes.items(), key=lambda x: x[1].activation)
        self.strongest_node = best[0]
        return best[0]

    def run_cycles(self, num: int = 8) -> None:
        """Run num cycles of propagate → relax → converge. Fast by design."""
        for _ in range(num):
            self.propagate()
            self.relax()
            self.converge()
        self.find_strongest()

    def coherence(self) -> float:
        """Simple coherence: mean activation."""
        if not self.nodes:
            return 0.0
        return sum(n.activation for n in self.nodes.values()) / len(self.nodes)

    def export_graph(self) -> Dict[str, Any]:
        """Export graph for BoggersTheOS: strongest_node, nodes, edges."""
        nodes_dict = {nid: n.to_dict() for nid, n in self.nodes.items()}
        edges_list = [{"src": a, "dst": b, "weight": w} for a, b, w in self.edges]
        return {
            "strongest_node": self.strongest_node,
            "nodes": nodes_dict,
            "edges": edges_list,
        }
