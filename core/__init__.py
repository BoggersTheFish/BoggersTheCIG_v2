"""BoggersTheCIG-v2 core: TS kernel, emergence, ingestor, mapper."""

from .ts_kernel import TSNode, TSKernel
from .emergence import run_emergence
from .ingestor import process_inbox, process_raw_text
from .mapper import build_edges

__all__ = ["TSNode", "TSKernel", "run_emergence", "process_inbox", "process_raw_text", "build_edges"]
