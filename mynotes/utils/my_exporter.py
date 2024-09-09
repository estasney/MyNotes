import argparse
import logging
import os
import os.path
from functools import partial
from pathlib import Path, PurePath

import nbformat
from config import Config as MyNotesConfig
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import desc
from traitlets.config import Config

from mynotes.notes_exporter.html import MyNotesHTMLExporter
from mynotes.notes_exporter.preprocess.codescan import ExtractModuleUsagePP
from mynotes.notes_exporter.preprocess.dates import NBDateProcessorPP
from mynotes.notes_exporter.preprocess.keyword import KeywordPreprocessorPP
from mynotes.notes_exporter.preprocess.metadata import MyNotesMetadataPP
from mynotes.notes_exporter.preprocess.remove_execution_count import (
    RemoveExecutionCountPP,
)
from mynotes.notes_exporter.preprocess.title import NBTitleMarkdownPP
from mynotes.notes_exporter.utils import ignored_category
from mynotes.utils.hasher import hashed_filename
from mynotes.utils.preprocess import category_name, nb_display_name
from mynotes.utils.storage.models.meta import Session, get_session
from mynotes.utils.storage.models.model import Category, Keyword, Module, Notebook

env = Environment(
    loader=FileSystemLoader(
        [
            Path(__file__).parent.parent / "templates",
            Path(__file__).parent.parent / "export" / "templates",
        ]
    ),
    autoescape=select_autoescape(["html"]),
    extensions=["jinja2.ext.debug"],
)

logger = logging.getLogger(__name__)


def store_notebook(
    nb_obj: nbformat.notebooknode.NotebookNode,
    nb_name: str,
    nb_category: str,
    category_parents: list,
    nb_resources: dict,
    db_session: Session,
):
    nb_modules = nb_resources["mynotes"]["modules"]
    nb_keywords = nb_resources["mynotes"]["keywords"]
    nb_title = nb_resources["mynotes"]["title"]
    nb_description = nb_resources["mynotes"]["description"]
    nb_created = nb_resources["mynotes"]["created"]
    nb_updated = nb_resources["mynotes"]["updated"]
    if not nb_title:
        logger.warning("{} missing title".format(nb_name))
    if not nb_description:
        logger.info("{} missing description".format(nb_name))

    def get_module(f):
        obj = Module(name=f)
        db_obj = db_session.merge(obj)
        return db_obj

    def get_keyword(f):
        obj = Keyword(name=f)
        db_obj = db_session.merge(obj)
        return db_obj

    def get_category(f):
        obj = Category(name=f)
        db_obj = db_session.merge(obj)
        return db_obj

    module_objs = [get_module(m) for m in nb_modules]
    kw_objs = [get_keyword(kw) for kw in nb_keywords]
    nb_obj = Notebook(
        name=nb_name,
        description=nb_description,
        display_name=nb_display_name(nb_name),
        title=nb_title,
        created=nb_created,
        updated=nb_updated,
    )
    db_session.add(nb_obj)
    nb_obj.modules = module_objs
    nb_obj.keywords = kw_objs
    db_nb_category = get_category(nb_category)

    db_nb_category.notebooks.append(nb_obj)
    for module in module_objs:
        if module not in db_nb_category.modules:
            db_nb_category.modules.append(module)
    for kw in kw_objs:
        if kw not in db_nb_category.keywords:
            db_nb_category.keywords.append(kw)

    db_session.commit()


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
    notebooks = session.query(Notebook).order_by(desc(Notebook.created)).all()
    notebooks = [nb.to_dict() for nb in notebooks]
    base = env.get_template("base.html")
    base_render = base.render({"data": notebooks})
    config = MyNotesConfig()
    # fp = config.smart_path(config.INDEX_DIR, "index_built.html")
    fp = config.INDEX_DIR / "index_built.html"
    with open(fp, "w+", encoding="utf-8") as html_file:
        html_file.write(base_render)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate My Notes")
    parser.add_argument("--develop", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        format="%(name)s : %(message)s",
        level=logging.INFO,
    )

    my_config = MyNotesConfig()
    # my_config.clean()
    my_config.clean_db()

    session = get_session()
    store_categories(session)

    if args.develop:
        deploy_domain = "http://localhost:8000"
        public_path = "/static/dist/"

    else:
        deploy_domain = f"https://{my_config.DEPLOYMENT_DOMAIN}"
        public_path = "/MyNotes/static/dist/"

    env.globals.update({"domain": deploy_domain, "develop": args.develop})
    env.filters["resolve"] = partial(hashed_filename, url_prefix=public_path)
    env.trim_blocks = True
    env.lstrip_blocks = True
    custom_config = Config()
    custom_config.extra_loaders = env.loader
    custom_config.ClearMetadataPreprocessor.enabled = True
    custom_config.NotesExporter.preprocessors = [
        MyNotesMetadataPP,
        RemoveExecutionCountPP,
        ExtractModuleUsagePP(
            ignored=["os", "subprocess", "glob", "base64", "pathlib", "io"]
        ),
        KeywordPreprocessorPP,
        NBTitleMarkdownPP,
        NBDateProcessorPP,
    ]
    custom_config.TemplateExporter.exclude_input_prompt = True
    custom_config.TemplateExporter.exclude_output_prompt = True
    custom_config.NotesExporter.exclude_anchor_links = True

    for root, folders, files in os.walk(my_config.NOTES_DIR):
        p = Path(root)
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
        
        output_folder = my_config.PAGES_DIR.joinpath(*parents, category)
        os.makedirs(output_folder, exist_ok=True)

        notebooks = [f for f in files if f.endswith("ipynb")]
        for nb_file in notebooks:
            nb_file = Path(root) / nb_file
            nb_output_path = Path(output_folder) / nb_file.with_suffix(".html").name
            abs_path = os.path.join(root, nb_file)
            nb = nbformat.read(abs_path, as_version=4)
            html_exporter = MyNotesHTMLExporter(config=custom_config, env=env)
            (body, resources) = html_exporter.from_notebook_node(nb)
            store_notebook(
                nb_obj=nb,
                nb_name=nb_output_path.name,
                nb_category=category,
                category_parents=parents,
                nb_resources=resources,
                db_session=session,
            )

            html_exporter.body_to_template_base(body, str(nb_output_path))
            logging.info(f"Saved {nb_output_path}")

    create_index(session)
