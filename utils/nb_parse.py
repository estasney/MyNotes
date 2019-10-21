import json
from pygments import highlight
from pygments.lexers import PythonLexer, MarkdownLexer
from pygments.formatters.html import HtmlFormatter

class NBParser(object):

    def __init__(self, nb_path):
        self.nb_path = nb_path
        self.nb = self.read_notebook(nb_path)
        self.cells = [NBCell(cell) for cell in self.nb['cells']]

    def read_notebook(self, f: str):
        with open(f, "r") as nb:
            return json.load(nb)

class NBCell(object):

    def __init__(self, cell: dict):
        self.cell = cell
        self.cell_type = cell['cell_type']
        self._source = cell['source']
        self._output = cell.get('outputs')

    @property
    def is_code(self):
        return self.cell_type == 'code'

    @property
    def is_markdown(self):
        return self.cell_type == 'markdown'

    # TODO output

    @property
    def source(self):
        code = "\n".join(self._source)
        if self.is_code:
            return highlight(code, PythonLexer(), HtmlFormatter())
        else:
            return highlight(code, MarkdownLexer(), HtmlFormatter())





def get_nb_cells(nb: dict) -> list:
    return