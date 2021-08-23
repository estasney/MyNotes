from jinja2 import Environment, PackageLoader, select_autoescape
from bs4 import BeautifulSoup

env = Environment(
    loader=PackageLoader("mynotes", "templates"), autoescape=select_autoescape(["html"])
)


def extract_nb_body(fp: str):
    with open(fp, "r") as nb_html:
        soup = BeautifulSoup(nb_html.read())
