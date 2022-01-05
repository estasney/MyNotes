from nbconvert.preprocessors import Preprocessor


class MyNotesData(Preprocessor):
    """Add a chainmap for mynotes"""

    def preprocess(self, nb, resources):
        resources["mynotes"] = {
            "keywords": [],
            "modules": [],
            "title": "",
            "description": "",
            "created": None,
            "updated": None,
        }
        return nb, resources
