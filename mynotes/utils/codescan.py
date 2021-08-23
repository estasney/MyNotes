from typing import List, Tuple, Type, Optional
from collections import namedtuple
import nbformat
from pygments.lexers.python import PythonLexer
from typing import Union
import re

NB = Union[nbformat.notebooknode.NotebookNode, str]

lexer = PythonLexer()
Token = namedtuple("Token", "token_type text")

kn = "Token.Keyword.Namespace"
nn = "Token.Name.Namespace"
t = "Token.Text"


def scan_line_modules(line: str) -> list:
    """
    Scan a cell line for modules imported
    Parameters
    ----------
    line

    Returns
    -------
    Modules found
    """

    if not any([x in line for x in ["from", "import"]]):
        return []

    tokens = _parse_line(line)
    found = _read_parsed(tokens)
    return found


def scan_nb_markdown(nb: NB) -> Tuple:
    """
    Scan a notebook's markdown cells for a 'title' and 'description'
    # Title

    Parameters
    ----------
    nb
        Either a NotebookNode or a path-like string
    """

    if isinstance(nb, str):
        nb = nbformat.read(nb, as_version=4)

    cells = [
        cell.get("source", None)
        for cell in nb["cells"]
        if cell.get("cell_type", "") == "markdown"
    ]
    title_match = re.compile(r"\A\s?(#)")
    description_match = re.compile(r"(?<=\*)(.*)(?=\*)")
    title_cell = next((cell for cell in cells if title_match.search(cell)), None)
    if not title_cell:
        return None, None
    title = next(
        (
            line
            for line in title_cell
            if title_match.search(line)
            for line in title_cell.splitlines()
        ),
        None,
    )
    description = description_match.findall(title_cell)
    if description:
        description = description[0]
    else:
        description = None
    if title:
        title = title_match.sub("", title).strip()
    return title, description


def scan_nb_code(nb: NB) -> List[Optional[str]]:
    """
    Scan a notebook's code cells for modules imported
    Parameters
    ----------
    nb: NB
        Either a NotebookNode or a path-like string
    """
    if isinstance(nb, str):
        nb = nbformat.read(nb, as_version=4)
    cells = [
        cell.get("source", "")
        for cell in nb["cells"]
        if cell.get("cell_type", "") == "code"
    ]
    cell_modules = [scan_line_modules(cell) for cell in cells]
    # flatten and remove duplicates
    return list(set([module for cell_module in cell_modules for module in cell_module]))


def scan_nb_keywords(nb: NB) -> List[Optional[str]]:
    """
    Scan a notebook's markdown cells for <keyword></keyword> tags
    Parameters
    ----------
    nb: NB
        Either a NotebookNode or a path-like string


    Returns
    -------

    """
    if isinstance(nb, str):
        nb = nbformat.read(nb, as_version=4)
    keyword_search = re.compile(r"(?<=<keyword>).+?(?=</keyword>)")
    cells = [
        cell.get("source", "")
        for cell in nb["cells"]
        if cell.get("cell_type", "") == "markdown"
    ]
    keywords = [keyword_search.findall(cell) for cell in cells]
    # flatten and remove duplicates
    return list(set([module for cell_module in keywords for module in cell_module]))


def _format_tokens(tokens: list):
    tokens = [(str(x[0]), x[1]) for x in tokens]
    tokens = [t for t in tokens if t[1] != " "]
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
            if tokens[(i - 1)].text in ["import", ",", "from"]:
                output.append(token.text)
            else:
                continue
    return output
