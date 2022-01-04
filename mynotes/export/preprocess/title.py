import re

from nbconvert.preprocessors import Preprocessor


class NBTitleMarkdown(Preprocessor):
    TITLE_MATCH = re.compile(r"(?<=#\s)(.*)")

    def preprocess(self, nb, resources):
        for cell in nb.cells:
            if cell.cell_type == "markdown" and self.TITLE_MATCH.search(cell.source):
                metadata = resources.get("metadata", {})
                metadata["title"] = self.TITLE_MATCH.search(cell.source).group()
                resources["metadata"] = metadata
                break
        return nb, resources
