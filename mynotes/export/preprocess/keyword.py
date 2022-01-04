import re

from nbconvert.preprocessors import Preprocessor


class KeywordPreprocessor(Preprocessor):
    KEYWORD_SEARCH = re.compile(r"(?<=<keyword>).+?(?=</keyword>)")

    def preprocess_cell(self, cell, resources, index):
        """Extract keywords"""
        if cell.cell_type == "markdown":
            keywords = self.KEYWORD_SEARCH.findall(cell.source)
            if keywords:
                resources['keywords'] = keywords
                print(f"Keyword {keywords}")
        return cell, resources

