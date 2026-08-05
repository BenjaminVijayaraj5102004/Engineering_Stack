import uuid
from ...builders.main_builder import build_main_agent
from ...util.logger import get_logger

logger = get_logger(__name__)

main_agent = build_main_agent()
