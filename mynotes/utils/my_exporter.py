import os
import os.path

import nbformat
from nbconvert import HTMLExporter

from jinja2 import Environment, PackageLoader, select_autoescape
from bs4 import BeautifulSoup
from pathlib import PurePath

from mynotes.utils.codescan import scan_nb_code, scan_nb_markdown
from mynotes.utils.storage.models.model import Notebook, Category, Module
from mynotes.utils.storage.models.meta import get_session, Session
from config import Config as MyNotesConfig

env = Environment(
        loader=PackageLoader('mynotes', 'templates'),
        autoescape=select_autoescape(['html'])
        )


def store_notebook(nb: nbformat.notebooknode.NotebookNode, nb_name: str, category: str, category_parents: list,
                   session: Session):
    nb_modules = scan_nb_code(nb)
    nb_title = scan_nb_markdown(nb)
    if not nb_title:
        print("{} missing title".format(nb_name))

    def get_module(f):
        m = session.query(Module).filter(Module.name == f).first()
        if not m:
            m = Module(name=f)
            session.add(m)
            session.commit()
        return m

    module_objs = [get_module(m) for m in nb_modules]
    nb_obj = Notebook(name=nb_name, display_name=nb_name.replace("_", " ").replace(".html", "").title(), title=nb_title)
    session.add(nb_obj)
    nb_obj.modules = module_objs

    nb_category_query = session.query(Category).filter(Category.name == category)
    if category_parents:
        nb_category_query = nb_category_query.filter(Category.parent.has(Category.name == category_parents[-1]))
    category_obj = nb_category_query.first()
    if not category_obj:
        raise Exception("Category not found")

    category_obj.notebooks.append(nb_obj)
    for module in module_objs:
        if module not in category_obj.modules:
            category_obj.modules.append(module)

    session.commit()


def store_categories(session: Session):
    my_config = MyNotesConfig()

    def filter_folders(x):
        if x == 'notes' or x.startswith('.'):
            return False
        return True

    def get_category(f):
        c = session.query(Category).filter(Category.name == f).first()
        if not c:
            c = Category(name=f, display_name=f.replace("_", " ").title())
            session.add(c)
        return c

    for dir, folders, _ in os.walk(my_config.NOTES_DIR):
        p = PurePath(dir)
        parent_name = p.name if filter_folders(p.name) else None
        category_folders = [f for f in folders if filter_folders(f)]
        if not category_folders:
            continue
        category_objs = [get_category(f) for f in category_folders]
        for c in category_objs:
            session.add(c)
        if parent_name:
            parent_obj = session.query(Category).filter(Category.name == parent_name).first()
            if not parent_obj:
                parent_obj = Category(name=parent_name, display_name=parent_name.replace("_", " ").title())
                session.add(parent_obj)
            parent_obj.children_categories = category_objs
        session.commit()
    session.commit()


def create_index(session: Session):
    categories = session.query(Category).filter(Category.parent_id == None).all()
    categories = [c.to_dict() for c in categories]
    base = env.get_template("base.html")
    base_render = base.render({'data': categories})
    config = MyNotesConfig()
    fp = config.smart_path(config.PAGES_DIR, "index.html")
    with open(fp, "w+", encoding="utf-8") as html_file:
        html_file.write(base_render)


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

    def body_to_template_base(self, body: str, fp: str):
        """
        We want the rendered body to be included in a MyNotes template.

        Pass the HTML text returned after calling self.from_notebook_node

        """

        soup = BeautifulSoup(body, features='lxml')
        body = soup.find("body")
        try:
            title = soup.find("h1").text.encode('ascii', errors='ignore').decode()
        except AttributeError:
            title = ""
        base = env.get_template("note_base.html")
        # //span[@class='nn'][not(preceding-sibling::span[contains(text(), 'as')])]
        base_str = base.render(title=title, content=str(body))
        with open(fp, "w+", encoding="utf-8") as html_file:
            html_file.write(base_str)


if __name__ == '__main__':

    my_config = MyNotesConfig()
    my_config.clean()
    my_config.clean_db()
    session = get_session()
    store_categories(session)

    for dir, folders, files in os.walk(my_config.NOTES_DIR):
        p = PurePath(dir)
        category = p.name
        if category in ['notes', '.ipynb_checkpoints']:
            continue

        # Determine if this category has any parents
        # Work up the tree until we reach 'notes'
        parents = []
        for parent in [x.name for x in p.parents]:
            if parent in ['notes', '.ipynb_checkpoints']:
                break
            parents.append(parent)

        # Reverse the order so list is parent -> child
        parents = list(reversed(parents))

        output_folder = my_config.smart_path(my_config.PAGES_DIR, *parents, category)
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)

        notebooks = [f for f in files if f.endswith("ipynb")]
        for nb_file in notebooks:
            nb_name = os.path.splitext(nb_file)[0]
            nb_output_name = nb_name + ".html"
            abs_path = os.path.join(dir, nb_file)

            output_path = my_config.smart_path(output_folder, nb_output_name)
            V = 4
            nb = nbformat.read(abs_path, as_version=V)
            store_notebook(nb=nb, nb_name=nb_output_name, category=category, category_parents=parents, session=session)

            html_exporter = NotesExporter()
            (body, r) = html_exporter.from_notebook_node(nb)
            html_exporter.body_to_template_base(body, output_path)

    create_index(session)
