from typing import TYPE_CHECKING

from nbconvert.preprocessors import Preprocessor

if TYPE_CHECKING:
    from nbformat import NotebookNode
    
class MyNotesMetadataPP(Preprocessor):
    """Add a chainmap for mynotes"""

    def preprocess(self, nb: "NotebookNode", resources: dict) -> tuple["NotebookNode", dict]:
        resources["mynotes"] = {
            "keywords": [],
            "modules": [],
            "title": "",
            "description": "",
            "created": None,
            "updated": None,
        }
        return nb, resources
