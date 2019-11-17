import os
import os.path

from traitlets.config import Config
from nbconvert.exporters.html import HTMLExporter

from jinja2 import Environment, PackageLoader, select_autoescape
from bs4 import BeautifulSoup

env = Environment(
        loader=PackageLoader('mynotes', 'templates'),
        autoescape=select_autoescape(['html'])
        )


class NotesExporter(HTMLExporter):
    """
    Export Notes to HTML
    """

    # If this custom exporter should add an entry to the
    # "File -> Download as" menu in the notebook, give it a name here in the
    # `export_from_notebook` class member
    export_from_notebook = "Notes Format"

    def _file_extension_default(self):
        """
        The new file extension is `.test_ext`
        """
        return '.html'

    @property
    def template_path(self):
        """
        We want to inherit from HTML template, and have template under
        `./templates/` so append it to the search path. (see next section)
        """
        return super().template_path + [os.path.join(os.path.dirname(__file__), "templates")]

    def _template_file_default(self):
        """
        We want to use the new template we ship with our library.
        """
        return 'notes'  # full

    def body_to_template_base(self, body: str, fp: str, title: str):
        """
        We want the rendered body to be included in a MyNotes template.

        Pass the HTML text returned after calling self.from_notebook_node

        """

        soup = BeautifulSoup(body, features='lxml')
        body = soup.find("body")
        base = env.get_template("base.html")
        base_str = base.render(title=title, content=str(body))
        with open(fp, "w+", encoding="utf-8") as html_file:
            html_file.write(base_str)


if __name__ == '__main__':
    import nbformat
    import nbconvert
    from nbconvert import HTMLExporter
    from mynotes.config import Config as MyNotesConfig
    from traitlets.config import Config

    my_config = MyNotesConfig()

    f = my_config.smart_path(my_config.NOTES_DIR, "pandas", "filtering.ipynb")
    fout = my_config.smart_path(my_config.PAGES_DIR, "filtering.html")
    V = 4

    nb = nbformat.read(f, as_version=V)
    html_exporter = NotesExporter()
    (body, r) = html_exporter.from_notebook_node(nb)
    html_exporter.body_to_template_base(body, fout, "Filtering")
    with open(my_config.smart_path(my_config.NOTES_DIR, "pandas", "filtering.html"), "w+") as fp:
        fp.write(body)
