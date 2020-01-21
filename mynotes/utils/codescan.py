from typing import List
from collections import namedtuple
import nbformat
from pygments.lexers.python import PythonLexer
from typing import Union

NB = Union[nbformat.notebooknode.NotebookNode, str]

lexer = PythonLexer()
Token = namedtuple('Token', 'token_type text')

kn = 'Token.Keyword.Namespace'
nn = 'Token.Name.Namespace'
t = 'Token.Text'


def scan_line(line: str) -> list:
    """
    Scan a cell line for modules imported
    Parameters
    ----------
    line

    Returns
    -------
    Modules found
    """

    if not any([x in line for x in ['from', 'import']]):
        return []

    tokens = _parse_line(line)
    found = _read_parsed(tokens)
    return found


def scan_nb(nb: NB) -> list:
    """
    Scan a notebooks code cells for modules imported
    Parameters
    ----------
    nb
        Either a NotebookNode or a path-like string
    """
    if isinstance(nb, str):
        nb = nbformat.read(nb, as_version=4)
    cells = [cell.get('source', '') for cell in nb['cells'] if cell.get('cell_type', '') == 'code']
    cell_modules = [scan_line(cell) for cell in cells]
    # flatten and remove duplicates
    return list(set([module for cell_module in cell_modules for module in cell_module]))


def _format_tokens(tokens: list):
    tokens = [(str(x[0]), x[1]) for x in tokens]
    tokens = [t for t in tokens if t[1] != ' ']
    tokens = [Token(token_type=t[0], text=t[1]) for t in tokens]
    return tokens


def _parse_line(x):
    return _format_tokens(lexer.get_tokens(x))


def _read_parsed(tokens: List[Token]):
    # first token should be a Namespace
    output = []
    if tokens[0].token_type != kn:
        return output
    # Continue to next nn
    for i, token in enumerate(tokens[1:], start=1):
        if token.token_type == nn:
            # is it following a namespace?
            if tokens[(i - 1)].text in ['import', ',', 'from']:
                output.append(token.text)
            else:
                continue
    return output
