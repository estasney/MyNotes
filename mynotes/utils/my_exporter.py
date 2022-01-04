import argparse
import os
import os.path
import logging

import nbformat
from mynotes.export import NotesExporter
from nbconvert import HTMLExporter
from functools import partial

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape
from bs4 import BeautifulSoup
from pathlib import Path, PurePath

from nbconvert.preprocessors import Preprocessor
from traitlets.config import Config

from mynotes.export.preprocess.keyword import KeywordPreprocessor
from mynotes.export.preprocess.remove_execution_count import RemoveExecutionCount
from mynotes.export.preprocess.title import NBTitleMarkdown
from mynotes.export.utils import ignored_category
from mynotes.utils.codescan import scan_nb_code, scan_nb_markdown, scan_nb_keywords
from mynotes.utils.preprocess import nb_display_name, category_name
from mynotes.utils.static_handler import copy_static_folder
from mynotes.utils.storage.models.model import Notebook, Category, Module, Keyword
from mynotes.utils.storage.models.meta import get_session, Session
from mynotes.utils.hasher import hash_folder, hashed_filename
from config import Config as MyNotesConfig

env = Environment(
    loader=FileSystemLoader([Path(__file__).parent.parent / "templates", Path(__file__).parent.parent / "export" / "templates"]),
    autoescape=select_autoescape(["html"]),
    extensions=["jinja2.ext.debug"],
)

logger = logging.getLogger(__name__)


def store_notebook(
    nb: nbformat.notebooknode.NotebookNode,
    nb_name: str,
    category: str,
    category_parents: list,
    session: Session,
):
    nb_modules = scan_nb_code(nb)
    nb_keywords = scan_nb_keywords(nb)
    nb_title, nb_description = scan_nb_markdown(nb)
    if not nb_title:
        logger.warning("{} missing title".format(nb_name))
    if not nb_description:
        logger.info("{} missing description".format(nb_name))

    def get_module(f):
        m = session.query(Module).filter(Module.name == f).first()
        if not m:
            m = Module(name=f)
            session.add(m)
            session.commit()
        return m

    def get_keyword(f):
        kw = session.query(Keyword).filter(Keyword.name == f).first()
        if not kw:
            kw = Keyword(name=f)
            session.add(kw)
            session.commit()
        return kw

    module_objs = [get_module(m) for m in nb_modules]
    kw_objs = [get_keyword(kw) for kw in nb_keywords]
    nb_obj = Notebook(
        name=nb_name,
        description=nb_description,
        display_name=nb_display_name(nb_name),
        title=nb_title,
    )
    session.add(nb_obj)
    nb_obj.modules = module_objs
    nb_obj.keywords = kw_objs

    nb_category_query = session.query(Category).filter(Category.name == category)
    if category_parents:
        nb_category_query = nb_category_query.filter(
            Category.parent.has(Category.name == category_parents[-1])
        )
    category_obj = nb_category_query.first()
    if not category_obj:
        raise Exception("Category not found")

    category_obj.notebooks.append(nb_obj)
    for module in module_objs:
        if module not in category_obj.modules:
            category_obj.modules.append(module)
    for kw in kw_objs:
        if kw not in category_obj.keywords:
            category_obj.keywords.append(kw)

    session.commit()


def store_categories(session: Session):
    my_config = MyNotesConfig()

    def filter_folders(x):
        if x == "notes" or x.startswith("."):
            return False
        return True

    def get_category(f):
        c = session.query(Category).filter(Category.name == f).first()
        if not c:
            c = Category(name=f, display_name=category_name(f))
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
            parent_obj = (
                session.query(Category).filter(Category.name == parent_name).first()
            )
            if not parent_obj:
                parent_obj = Category(
                    name=parent_name, display_name=category_name(parent_name)
                )
                session.add(parent_obj)
            parent_obj.children_categories = category_objs
        session.commit()
    session.commit()


def create_index(session: Session):
    categories = session.query(Category).filter(Category.parent_id == None).all()
    categories = [c.to_dict() for c in categories]
    base = env.get_template("base.html")
    base_render = base.render({"data": categories})
    config = MyNotesConfig()
    fp = config.smart_path(config.PAGES_DIR, "index.html")
    with open(fp, "w+", encoding="utf-8") as html_file:
        html_file.write(base_render)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate My Notes")
    parser.add_argument("--develop", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)s : %(levelname)s : %(message)s",
        level=logging.DEBUG,
    )
    logger.addHandler(logging.StreamHandler())
    my_config = MyNotesConfig()
    my_config.clean()
    my_config.clean_db()

    copy_static_folder(my_config.STATIC_SRC, my_config.STATIC_DIST)

    session = get_session()
    store_categories(session)

    if args.develop:
        deploy_domain = "http://localhost:8000/"
        deploy_style = "{}static/dist/".format(deploy_domain)
    else:
        deploy_domain = "//{}/".format(my_config.DEPLOYMENT_DOMAIN)
        deploy_style = "{}static/dist/".format(deploy_domain)

    env.globals.update({"domain": deploy_domain, "develop": args.develop})
    env.filters["resolve"] = partial(hashed_filename, url_prefix=deploy_style)
    env.trim_blocks = True
    env.lstrip_blocks = True
    custom_config = Config()
    custom_config.extra_loaders = env.loader
    custom_config.ClearMetadataPreprocessor.enabled = True
    custom_config.NotesExporter.preprocessors = [RemoveExecutionCount, KeywordPreprocessor, NBTitleMarkdown]
    custom_config.TemplateExporter.exclude_input_prompt = True
    custom_config.TemplateExporter.exclude_output_prompt = True
    custom_config.NotesExporter.exclude_anchor_links = True

    for dir, folders, files in os.walk(my_config.NOTES_DIR):
        p = Path(dir)
        category = p.name
        if ignored_category(category):
            continue

        # Determine if this category has any parents
        # Work up the tree until we reach 'notes'
        parents = []
        for parent in [x.name for x in p.parents]:
            if ignored_category(parent):
                break
            parents.append(parent)

        # Reverse the order so list is parent -> child
        parents = list(reversed(parents))

        output_folder = my_config.smart_path(my_config.PAGES_DIR, *parents, category)
        os.makedirs(output_folder, exist_ok=True)

        notebooks = [f for f in files if f.endswith("ipynb")]
        for nb_file in notebooks:
            nb_file = Path(dir) / nb_file
            nb_output_path = Path(output_folder) / nb_file.with_suffix(".html").name
            abs_path = os.path.join(dir, nb_file)
            nb = nbformat.read(abs_path, as_version=4)
            store_notebook(
                nb=nb,
                nb_name=nb_output_path.name,
                category=category,
                category_parents=parents,
                session=session,
            )

            html_exporter = NotesExporter(config=custom_config, env=env)
            (body, resources) = html_exporter.from_notebook_node(nb)
            html_exporter.body_to_template_base(body, str(nb_output_path))

    create_index(session)
