import os
import shutil

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    def __init__(self):
        self.BASE_DIR = basedir
        self.NOTES_DIR = self.smart_path("mynotes", "notes")
        self.PAGES_DIR = self.smart_path("docs")
        self.INDEX_DIR = self.smart_path("mynotes", "src")
        self.IGNORED_PAGES_DIR = ["static"]
        self.IGNORED_PAGES_FILES = [".nojekyll"]
        self.DB_PATH = self.smart_path("mynotes.db")
        self.DB_URL = "sqlite:///" + self.DB_PATH
        self.DEPLOYMENT_DOMAIN = "estasney.github.io/MyNotes"
        self.STATIC_SRC = self.smart_path("mynotes", "src", "dist")
        self.STATIC_DIST = self.smart_path(self.PAGES_DIR, "static", "dist")
        self.HASHED_DIRS = [self.STATIC_DIST]

    def smart_path(self, *args):
        return os.path.join(*[self.BASE_DIR, *args])

    def clean(self):
        """
        Delete everything in /docs except for directories in self.IGNORED_PAGES_DIR
        """
        # Get folder contents
        pages_contents = os.listdir(self.PAGES_DIR)

        # Remove ignored
        pages_contents = [
            f
            for f in pages_contents
            if f not in self.IGNORED_PAGES_DIR and f not in self.IGNORED_PAGES_FILES
        ]

        # Resolve to absolute path
        pages_contents = [os.path.join(self.PAGES_DIR, f) for f in pages_contents]

        # Separate into directories and files
        pages_contents_dirs = [f for f in pages_contents if os.path.isdir(f)]
        pages_contents_files = [f for f in pages_contents if os.path.isfile(f)]

        # Remove directories (even full)
        for folder in pages_contents_dirs:
            shutil.rmtree(folder, ignore_errors=True)

        # Remove files
        for file in pages_contents_files:
            os.remove(file)

    def clean_db(self):
        """
        Wipe the db
        """
        from mynotes.utils.storage.models.meta import Base, get_engine

        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        engine = get_engine()
        Base.metadata.create_all(engine)
