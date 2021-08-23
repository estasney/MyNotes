import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def copy_static_folder(src_folder, dist_folder):
    """

    Copy Contents of Webpack Generated dist folder
    Parameters
    ----------
    src_folder
        Location of Webpack generated files
    dist_folder
        Location to copy files to

    Returns
    -------
    None
    """
    logger.debug("Hashing folder {} to {}".format(src_folder, dist_folder))

    src_folder = Path(src_folder)
    dist_folder = Path(dist_folder)

    if not dist_folder.exists():
        dist_folder.mkdir(parents=True)

    # Erase contents of dist_folder
    for f in dist_folder.iterdir():
        logger.debug("Removing {}".format(str(f)))
        f.unlink()

    for f in src_folder.iterdir():
        f_out = dist_folder.joinpath(f.name)
        shutil.copyfile(str(f), str(f_out))
