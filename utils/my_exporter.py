import os
import os.path


from traitlets.config import Config
from nbconvert.exporters.html import HTMLExporter

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
        return super().template_path+[os.path.join(os.path.dirname(__file__), "templates")]

    def _template_file_default(self):
        """
        We want to use the new template we ship with our library.
        """
        return 'notes' # full

if __name__ == '__main__':
    import nbformat
    import nbconvert
    from nbconvert import HTMLExporter
    from traitlets.config import Config

    f = r"C:\Users\estasney\PycharmProjects\MyNotes\notes\pandas\filtering.ipynb"
    V = 4

    nb = nbformat.read(f, as_version=V)
    html_exporter = NotesExporter()
    (body, r) = html_exporter.from_notebook_node(nb)
    with open(r"C:\Users\estasney\PycharmProjects\MyNotes\notes\pandas\filtering.html", "w+") as fp:
        fp.write(body)
