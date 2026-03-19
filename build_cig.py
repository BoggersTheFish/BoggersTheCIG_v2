"""
BoggersTheCIG-v2 — Main orchestrator.
Load kernel → bootstrap if empty → ingestor (inbox) → mapper → 8 fast cycles → emergence → export.
Ultra-light for 5-min GitHub runs.
"""

import json
from pathlib import Path

from core.ts_kernel import TSKernel, VAULT_PATH
from core.emergence import run_emergence
from core.ingestor import Ingestor
from core.mapper import Mapper

SNAPSHOTS_DIR = "snapshots"
COHERENCE_LOG = "snapshots/coherence_log.jsonl"
GRAPH_JSON = "snapshots/graph.json"
COHERENCE_PNG = "snapshots/coherence-trend.png"
NUM_CYCLES = 8


def main() -> None:
    Path(SNAPSHOTS_DIR).mkdir(parents=True, exist_ok=True)

    kernel = TSKernel(vault_path=VAULT_PATH)
    kernel.scan_vault()

    # Bootstrap 6 deep nodes if vault empty (consciousness, AI, meta-cognition, etc.)
    if kernel.bootstrap_if_empty():
        kernel.scan_vault()

    ingestor = Ingestor()
    created = ingestor.process_inbox()
    print(f"📥 Ingested {len(created)} new notes from inbox")

    kernel.scan_vault()

    mapper = Mapper()
    mapper.build_edges(kernel)
    print(f"🔗 Built {len(kernel.edges)} smart edges")

    # 8 fast cycles
    coherence_history = []
    for i in range(NUM_CYCLES):
        kernel.propagate()
        kernel.relax()
        kernel.converge()
        coherence_history.append(kernel.coherence())
    kernel.find_strongest()

    # Emergence (creates new .md, adds to kernel)
    created = run_emergence(kernel, vault_path=VAULT_PATH)
    if created:
        # Quick re-run after emergence (2 extra cycles)
        for _ in range(2):
            kernel.propagate()
            kernel.relax()
            kernel.converge()
        kernel.find_strongest()
        coherence_history.append(kernel.coherence())
        coherence_history.append(kernel.coherence())

    # Export graph.json for BoggersTheOS
    graph = kernel.export_graph()
    with open(GRAPH_JSON, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    # Append to coherence log
    log_entry = {
        "coherence": kernel.coherence(),
        "strongest_node": kernel.strongest_node,
        "num_nodes": len(kernel.nodes),
        "num_edges": len(kernel.edges),
        "emerged": created,
    }
    with open(COHERENCE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    # coherence-trend.png
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 3))
        plt.plot(coherence_history, "b-", linewidth=2)
        plt.xlabel("Cycle")
        plt.ylabel("Coherence")
        plt.title("TS Coherence Trend")
        plt.tight_layout()
        plt.savefig(COHERENCE_PNG, dpi=80)
        plt.close()
    except Exception:
        pass

    print(f"CIG complete: {len(kernel.nodes)} nodes, strongest={kernel.strongest_node}")


if __name__ == "__main__":
    main()
