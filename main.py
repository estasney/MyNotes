import os
import subprocess
from enum import Enum
from functools import partial
from pathlib import Path

from mynotes_exporter.db import Notebook
from mynotes_exporter.settings import Settings
from mynotes_exporter.steps.notebook import process_notebook
from sqlalchemy import desc, select


class Environment(str, Enum):
    dev = "dev"
    prod = "prod"

    def __str__(self):
        return str.__str__(self)


HERE = Path(__file__).parent


def build_js(env: Environment):
    """
    We need to build and bundle the js files before we can export the notebooks. This way we get the hashed filename and
    make it available in the jinja2 template.
    """

    cmd = ["npm", "run", "build-prod" if env == Environment.prod else "build-dev"]
    build_dir = HERE / "web_src"

    with subprocess.Popen(
        cmd, cwd=build_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as proc:
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            print(stdout.decode("utf-8"))
            print(f"Error: {stderr.decode('utf-8')}")
            raise RuntimeError(f"Error building js files: {stderr.decode('utf-8')}")
        print(stdout.decode("utf-8"))
        print("Build complete")


def create_index_html(settings: Settings):
    session = settings.session
    query = select(Notebook).order_by(desc(Notebook.created))
    db_notebooks = session.execute(query).scalars().all()
    notebooks = [nb.to_dict() for nb in db_notebooks]
    base = settings.jinja_env.get_template("base.j2")
    base_render = base.render({"data": notebooks})

    output = HERE / "web_src" / "index_built.html"
    output.write_text(base_render, encoding="utf-8")

def start_dev_server():
    from http.server import SimpleHTTPRequestHandler
    class CORSRequestHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            SimpleHTTPRequestHandler.end_headers(self)

    import socketserver
    docs_directory = HERE / "docs"
    handler_class = partial(CORSRequestHandler, directory=docs_directory)
    with socketserver.TCPServer(("", 8000), handler_class) as httpd:
        try:
            print(f"Serving at port 8000, directory: {docs_directory}")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


      

def export(env: Environment):
    settings = Settings(
        notebook_dir=HERE / "notes",
        output_dir=HERE / "docs",
        nb_format_version=4,
        public_path="/MyNotes/static/dist/"
        if env == Environment.prod
        else "/static/dist/",
        deployment_domain="https://estasney.github.io/MyNotes"
        if env == Environment.prod
        else "http://localhost:8000",
        db_uri="sqlite:///mynotes.db",
        env="prod" if env == Environment.prod else "dev",
    )

    exporter = settings.exporter
    session = settings.session

    for root, _folders, files in os.walk(settings.notebook_dir):
        for file in files:
            if file.endswith(".ipynb"):
                file_path = Path(root) / file
                process_notebook(
                    file_path=file_path,
                    settings=settings,
                    exporter=exporter,
                    session=session,
                )
    create_index_html(settings=settings)
    build_js(env)
    if env == Environment.dev:
        start_dev_server()


if __name__ == "__main__":
    export(Environment.prod)
