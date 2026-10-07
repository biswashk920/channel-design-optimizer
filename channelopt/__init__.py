"""Channel Design Optimizer: uniform-flow design of open channels (Manning)."""
from .inputs import Inputs, InputError, NoSolution, load_linings
from .optimize import compare, design_section

__version__ = "0.1.0"
__all__ = ["Inputs", "InputError", "NoSolution", "load_linings",
           "compare", "design_section"]
