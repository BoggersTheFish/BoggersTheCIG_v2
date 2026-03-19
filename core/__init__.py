"""BoggersTheCIG-v2 core: TS kernel and emergence."""

from .ts_kernel import TSNode, TSKernel
from .emergence import run_emergence

__all__ = ["TSNode", "TSKernel", "run_emergence"]
