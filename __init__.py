"""
1038lab ComfyUI Node Loader
Automatically discovers, sorts, and registers nodes from current directory and py/
"""
from pathlib import Path
import sys
import importlib.util

__repo_name__ = "ComfyUI-Depth-Anything-3"
__version__ = "1.0.0"

# Locate current and node directories
current_dir = Path(__file__).parent
nodes_dir = current_dir / "py"

# Add both current and nodes directories to sys.path
for path in [current_dir, nodes_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Initialize mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
WEB_DIRECTORY = "./web"


def load_nodes():
    """Automatically discover and load node definitions recursively."""
    models_dir = current_dir / "models"
    
    for base in (current_dir, nodes_dir):
        if not base.exists():
            continue
        for file in base.rglob("*.py"):
            if file.stem == "__init__":
                continue
            # Defensively skip model checkpoint folders
            try:
                if file.is_relative_to(models_dir):
                    continue
            except Exception:
                if str(models_dir) in str(file):
                    continue

            module_name = file.stem
            try:
                spec = importlib.util.spec_from_file_location(module_name, file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    if hasattr(module, "NODE_CLASS_MAPPINGS"):
                        NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                    if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                        NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            except Exception as e:
                print(f"[{__repo_name__}] Error loading module {file.name}: {e}")


# Load all nodes
load_nodes()

# Alphabetically sort mappings by display name for a clean, consistent ComfyUI menu
NODE_CLASS_MAPPINGS = dict(
    sorted(
        NODE_CLASS_MAPPINGS.items(),
        key=lambda x: NODE_DISPLAY_NAME_MAPPINGS.get(x[0], x[0]),
    )
)
NODE_DISPLAY_NAME_MAPPINGS = dict(
    sorted(NODE_DISPLAY_NAME_MAPPINGS.items(), key=lambda x: x[1])
)

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# Formatted console branding on ComfyUI startup
print(f'\033[36m[{__repo_name__}]\033[0m v'
      f'\033[93m{__version__}\033[0m | '
      f'\033[37m{len(NODE_CLASS_MAPPINGS)} nodes\033[0m '
      f'\033[92mLoaded\033[0m')