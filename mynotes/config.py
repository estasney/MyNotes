import os
import pickle

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    def __init__(self):
        self.BASE_DIR = basedir
        self.NOTES_DIR = self.smart_path(self.BASE_DIR, "notes")
        self.PAGES_DIR = self.smart_path(self.BASE_DIR, "pages")

    def smart_path(self, *args):
        start_path = self.BASE_DIR
        for a in args:
            start_path = os.path.join(start_path, a)
        return start_path

if __name__ == '__main__':
    config = Config()
    for k, v in config.__dict__.items():
        if not k.startswith("_") and not k.endswith("_"):
            print("{} : {}".format(k, v))