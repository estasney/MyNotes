import re

from nbconvert.preprocessors import Preprocessor


class NBTitleMarkdown(Preprocessor):
    TITLE_MATCH = re.compile(r"(?<=#\s)(.*)")
    DESCRIPTION_MATCH = re.compile(r"(?<=\*)(.*)(?=\*)")

    def preprocess(self, nb, resources):
        target_cell = next((cell for cell in nb.cells if cell.cell_type == "markdown"))
        title_result = self.TITLE_MATCH.search(target_cell.source)
        desc_result = self.DESCRIPTION_MATCH.search(target_cell.source)
        if title_result:
            resources['mynotes']['title'] = title_result.group().strip()
        if desc_result:
            resources['mynotes']['description'] = desc_result.group().strip()
        return nb, resources
