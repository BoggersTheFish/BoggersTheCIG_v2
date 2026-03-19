# BoggersTheCIG-v2

**MAX-SPEED edition** — Deterministic TS infrastructure for the BoggersTheOS ecosystem.

## TS Rules (Strongest Node → Propagate → Relax → Converge → Emergence)

1. **Strongest Node** — Elect highest-activation node
2. **Propagate** — Wave propagation along edges
3. **Relax** — Decay toward base_strength
4. **Converge** — Prune edges < 0.25
5. **Emergence** — Detect clusters, auto-create new .md nodes

## One-Command Setup

```bash
pip install -r requirements.txt
python build_cig.py
```

## Outputs

- `snapshots/graph.json` — Full graph for BoggersTheOS (strongest_node, nodes, edges)
- `snapshots/coherence-trend.png` — Coherence over cycles
- `snapshots/coherence_log.jsonl` — Append-only coherence log
- `obsidian/TS-Knowledge-Vault/*.md` — Source of truth + emergent nodes

## Loading graph.json in BoggersTheOS

On boot, load `snapshots/graph.json`:

```python
import json
with open("snapshots/graph.json") as f:
    graph = json.load(f)
strongest = graph["strongest_node"]
nodes = graph["nodes"]
edges = graph["edges"]
```

Format: `nodes` is `{id: {base_strength, activation, attributes}}`, `edges` is `[{src, dst, weight}]`.

## Vault

Add `.md` files to `obsidian/TS-Knowledge-Vault/` with frontmatter:

```yaml
---
strength: 0.7
tags: [concept_a, concept_b]
---
```

## GitHub

Workflow runs every 5 minutes. Each run: 8 fast cycles, emergence, export. Commits only changed snapshots and new emergent .md files.
