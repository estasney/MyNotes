from nbconvert.preprocessors import Preprocessor
from pygments.lexers import get_lexer_by_name
from typing import Optional, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from pygments.token import Token


class ExtractModuleUsage(Preprocessor):
    """Find imported modules and add them to resources"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lexer = get_lexer_by_name("python")

    def preprocess(self, nb, resources):
        for index, cell in enumerate(nb.cells):
            nb.cells[index], resources = self.preprocess_cell(cell, resources, index)
        modules = resources["mynotes"]["modules"]
        if not modules:
            return nb, resources
        module_items = [item for item in modules]
        module_counts = Counter(module_items)
        module_items = list(set(module_items))
        module_items.sort(key=lambda x: module_counts.get(x), reverse=True)
        resources["mynotes"]["modules"] = module_items
        return nb, resources

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type != "code":
            return cell, resources
        tokens = self.lexer.get_tokens(cell.source)
        tokens = list(filter(self._filter_token, tokens))
        modules = ExtractModuleUsage._extract_modules(tokens)
        resources["mynotes"]["modules"].extend(modules)
        return cell, resources

    @staticmethod
    def _filter_token(token_chunk: tuple["Token", str]):
        """Filter individual tokens"""
        token, token_txt = token_chunk
        if token_txt.isspace():
            return False
        return True

    @staticmethod
    def _extract_modules(
        token_chunks: Optional[list[tuple["Token", str]]]
    ) -> list[str]:
        """Extract the module"""
        output = []
        if not token_chunks:
            return output
        if "Keyword.Namespace" not in str(token_chunks[0]):
            # This is not a valid import statement
            return output
        for i, (token, token_txt) in enumerate(token_chunks[1:], start=1):
            if "Name.Namespace" in str(token):
                # Is it following a namespace?
                if token_chunks[(i - 1)][1] in ("import", ",", "from"):
                    output.append(token_txt)
        return output
