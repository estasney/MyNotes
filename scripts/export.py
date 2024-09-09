import logging
import os
from argparse import ArgumentParser
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Type

import nbformat
import traitlets.config
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import desc, select
from toolz import curry, get_in

from mynotes import MyNotesHTMLExporter, Settings, get_session, get_settings
from mynotes.notes_exporter.db import Category, Keyword, Module, Notebook
from mynotes.notes_exporter.preprocess import (
    ExtractModuleUsagePP,
    KeywordPreprocessorPP,
    MyNotesMetadataPP,
    NBDateProcessorPP,
    NBTitleMarkdownPP,
    RemoveExecutionCountPP,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(name)s : %(message)s",
    level=logging.INFO,
)


def make_jinja_env(settings: Settings, is_dev: bool) -> Environment:
    env = Environment(
        loader=FileSystemLoader(
            [
                settings.PROJECT_DIR / "templates",
            ]
        ),
        autoescape=select_autoescape(["html"]),
        extensions=["jinja2.ext.debug"],
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def get_hashed_filename(file_name: str, url_prefix: str) -> str | None:
        src_search = settings.STATIC_DIST.rglob(file_name)
        matched_src = next(src_search, None)
        if not matched_src:
            logger.error("Found no src file matching {}".format(file_name))
            return None
        return url_prefix + matched_src.name

    env.globals.update({"domain": settings.DEPLOYMENT_DOMAIN, "develop": is_dev})
    env.filters["resolve"] = partial(
        get_hashed_filename, url_prefix=settings.PUBLIC_PATH
    )

    return env


def create_index(session: "Session", jinja_env: Environment, settings: "Settings") -> None:
    query = select(Notebook).order_by(desc(Notebook.created))
    db_notebooks = session.execute(query).scalars().all()
    notebooks = [nb.to_dict() for nb in db_notebooks]
    base = jinja_env.get_template("base.html")
    base_render = base.render({"data": notebooks})
    fp = settings.INDEX_DIR / "index_built.html"
    with open(fp, "w+", encoding="utf-8") as html_file:
        html_file.write(base_render)


def process_notebook(
        file_path: Path,
        settings: "Settings",
        exporter: "MyNotesHTMLExporter",
        session: "Session",
) -> None:
    base_path = settings.NOTES_DIR
    parents = file_path.parent.relative_to(base_path).parts

    output_folder = settings.PAGES_DIR.joinpath(*parents)
    os.makedirs(output_folder, exist_ok=True)
    nb_output_path = output_folder / file_path.with_suffix(".html").name
    nb_raw = nbformat.read(file_path, as_version=4)
    body, resources = exporter.from_notebook_node(nb_raw)

    modules = get_in(["mynotes", "modules"], resources, [])
    keywords = get_in(["mynotes", "keywords"], resources, [])
    title = get_in(["mynotes", "title"], resources, "")
    description = get_in(["mynotes", "description"], resources, "")
    created = get_in(["mynotes", "created"], resources, None)
    updated = get_in(["mynotes", "updated"], resources, None)
    if not title:
        logger.warning(f"Notebook {file_path} has no title")
    if not description:
        logger.warning(f"Notebook {file_path} has no description")

    @curry
    def get_model_obj[T](model_cls: Type[T], name: str) -> T:
        obj = model_cls(name=name)
        db_obj = session.merge(obj)
        return db_obj

    get_module = get_model_obj(Module)
    get_keyword = get_model_obj(Keyword)
    get_category = get_model_obj(Category)

    db_modules = [get_module(m) for m in modules]
    db_keywords = [get_keyword(kw) for kw in keywords]
    db_nb = Notebook(
        name=nb_output_path.name,
        description=description,
        display_name=nb_output_path.name,
        title=title,
        created=created,
        updated=updated,
    )
    session.add(db_nb)
    session.commit()
    db_nb.modules = db_modules
    db_nb.keywords = db_keywords
    session.commit()

    db_category = get_category(parents[-1])
    db_category.notebooks.append(db_nb)
    session.commit()

    db_category_modules = {module.name for module in db_category.modules}
    db_category_keywords = {keyword.name for keyword in db_category.keywords}

    if db_category_modules - {module.name for module in db_modules}:
        db_category.modules.extend(db_modules)
    if db_category_keywords - {keyword.name for keyword in db_keywords}:
        db_category.keywords.extend(db_keywords)

    session.commit()

    exporter.body_to_template_base(body, str(nb_output_path))
    logging.info(f"Saved {nb_output_path}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Generate My Notes")
    parser.add_argument("--develop", action="store_true")
    args = parser.parse_args()
    if args.develop:
        settings = get_settings(
            DEPLOYMENT_DOMAIN="http://localhost:8000", PUBLIC_PATH="/static/dist/"
        )

    else:
        settings = get_settings()
    jinja_env = make_jinja_env(settings, args.develop)
    db_session = get_session()
    custom_config = traitlets.config.Config()
    custom_config.extra_loaders = jinja_env.loader
    custom_config.ClearMetadataPreprocessor.enabled = True
    custom_config.MyNotesHTMLExporter.preprocessors = [
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

    exporter = MyNotesHTMLExporter(config=custom_config, env=jinja_env)

    for root, folders, files in os.walk(settings.NOTES_DIR):
        for file in files:
            if file.endswith("ipynb"):
                file_path = Path(root) / file
                process_notebook(
                    file_path=file_path,
                    settings=settings,
                    exporter=exporter,
                    session=db_session,
                )

    create_index(db_session, jinja_env, settings)
