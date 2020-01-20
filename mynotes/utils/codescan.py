from typing import List
from collections import namedtuple
from pygments.lexers.python import PythonLexer

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
