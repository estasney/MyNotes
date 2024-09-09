from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from nbconvert import HTMLExporter

if TYPE_CHECKING:
    from jinja2 import Environment


class MyNotesHTMLExporter(HTMLExporter):
    """
    Export Notes to HTML
    """

    def __init__(self, env: "Environment", **kw: dict | None) -> None:
        super().__init__(**kw)
        self.env = env

    def body_to_template_base(self, body: str, fp: str) -> None:
        """
        We want the rendered body to be included in a MyNotes template.
        This is an escape hatch from nbconvert.
        """

        soup = BeautifulSoup(body, features="lxml")
        body = soup.find("body")
        body.attrs = None
        title = soup.select_one("h1").text
        base = self.env.get_template("note_base.html")
        base_str = base.render(title=title, content=str(body).replace("\r", ""))
        with open(fp, "w+", encoding="utf-8") as html_file:
            html_file.write(base_str)
