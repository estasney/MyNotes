from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from typing import TYPE_CHECKING

from nbconvert.filters import Highlight2HTML
from nbconvert.filters.widgetsdatatypefilter import WidgetsDataTypeFilter

if TYPE_CHECKING:
    from jinja2.environment import Environment


class NotesExporter(HTMLExporter):
    """
    Export Notes to HTML
    """

    def __init__(self, env: "Environment", **kw):
        super().__init__(**kw)
        self.env = env

    def body_to_template_base(self, body: str | Path, fp: str):
        """
        We want the rendered body to be included in a MyNotes template.
        Pass the HTML text returned after calling self.from_notebook_node
        """

        soup = BeautifulSoup(body, features="lxml")
        body = soup.find("body")
        body.attrs = None
        title = soup.select_one("h1").text
        base = self.env.get_template("note_base.html")
        base_str = base.render(title=title, content=str(body).replace("\r", ""))
        with open(fp, "w+", encoding="utf-8") as html_file:
            html_file.write(base_str)
