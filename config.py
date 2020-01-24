import os
import shutil

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    def __init__(self):
        self.BASE_DIR = basedir
        self.NOTES_DIR = self.smart_path("mynotes", "notes")
        self.PAGES_DIR = self.smart_path("docs")
        self.IGNORED_PAGES_DIR = ['static']
        self.IGNORED_PAGES_FILES = []
        self.DB_PATH = self.smart_path('mynotes.db')
        self.DB_URL = "sqlite:///" + self.DB_PATH

    def smart_path(self, *args):
        start_path = self.BASE_DIR
        for a in args:
            start_path = os.path.join(start_path, a)
        return start_path

    def clean(self):
        """
        Delete everything in /docs except for directories in self.IGNORED_PAGES_DIR
        """
        # Get folder contents
        pages_contents = os.listdir(self.PAGES_DIR)

        # Remove ignored
        pages_contents = [f for f in pages_contents if
                          f not in self.IGNORED_PAGES_DIR and f not in self.IGNORED_PAGES_FILES]

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
        from mynotes.utils import get_engine, Base
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        engine = get_engine()
        Base.metadata.create_all(engine)


if __name__ == '__main__':
    config = Config()
    for k, v in config.__dict__.items():
        if not k.startswith("_") and not k.endswith("_"):
            print("{} : {}".format(k, v))
