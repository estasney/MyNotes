import re
from collections import Counter

from nbconvert.preprocessors import Preprocessor


class KeywordPreprocessor(Preprocessor):
    KEYWORD_SEARCH = re.compile(r"(?<=<keyword>).+?(?=</keyword>)")

    def preprocess(self, nb, resources):
        for index, cell in enumerate(nb.cells):
            nb.cells[index], resources = self.preprocess_cell(cell, resources, index)
        keywords = resources['mynotes']['keywords']
        if not keywords:
            return nb, resources
        keyword_items = [item for item in keywords]
        module_counts = Counter(keyword_items)
        keyword_items.sort(key=lambda x: module_counts.get(x), reverse=True)
        resources['mynotes']['keywords'] = keyword_items
        return nb, resources

    def preprocess_cell(self, cell, resources, index):
        """Extract keywords"""
        if cell.cell_type == "markdown":
            keywords = self.KEYWORD_SEARCH.findall(cell.source)
            if keywords:
                resources['mynotes']['keywords'].extend(keywords)
        return cell, resources

