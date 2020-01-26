from mynotes.utils.storage.models.model import Notebook, Module, Category
from mynotes.utils.storage.models.meta import get_session, get_engine
import logging

logger = logging.getLogger('mynotes')
if len(logger.handlers) == 0:  # To ensure reload() doesn't add another one
    logger.addHandler(logging.NullHandler())
