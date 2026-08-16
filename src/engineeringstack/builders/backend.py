from pathlib import Path
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from ..util.logger import get_logger

logger = get_logger(__name__)


SDK_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def build_default_backend() -> CompositeBackend:
    """Builds a composite backend that mounts the SDK internal skills directory."""
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/skills/": FilesystemBackend(root_dir=str(SDK_SKILLS_DIR)),
        },
    )
