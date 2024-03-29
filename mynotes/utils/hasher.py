from config import Config
import os
import hashlib
import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def _hash_file(file_path: str) -> str:
    with open(file_path, "rb") as fp:
        doc = fp.read()
        hashed = hashlib.md5(doc)
    hashed_hex = hashed.hexdigest()
    logger.debug("Hashed {} to {}".format(file_path, hashed_hex))
    return hashed_hex


def _is_hashed_variant(x, y):
    try:
        xname = re.search("^([^.]+)", x.name).group()
        yname = re.search("^([^.]+)", y.name).group()
        return xname == yname
    except AttributeError:
        logger.exception("")
        return False


def hashed_filename(file_name, url_prefix):
    """
    Intended to be called from a template. Given a filename, return the corresponding hashed filepath

    Parameters
    ----------
    file_name
        name of file


    Returns
    -------
        Corresponding hashed filepath

    Examples
    --------
    ```python
    hashed_filename("bootstrap.css")
    ```


    """
    config = Config()
    src_search = Path(config.STATIC_DIST).glob(file_name)
    matched_src = next(src_search, None)
    if not matched_src:
        logger.error("Found no src file matching {}".format(file_name))
        return None

    # find the corresponding hashed file
    return url_prefix + matched_src.name
