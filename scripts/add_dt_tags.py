import os
import nbformat
from pathlib import Path


def find_notebooks(folder):
    nb = []
    for dir, folders, files in os.walk(folder):
        parent_folder = Path(dir)
        files = [Path(f) for f in files]
        for file in files:
            if file.suffix == ".ipynb":
                nb.append(parent_folder / file)
    return nb


def add_tags(fp):
    nb = nbformat.read(fp, 4)
    cell = nb["cells"][0]
    if cell["cell_type"] != "markdown":
        print(f"{fp.name} does not have leading markdown cell -- skipping")
        return
    cell_source = cell["source"]
    updated = False
    if "<created>" not in cell_source:
        cell_source = f"{cell_source}\n<created></created>"
        updated = True
    if "<updated>" not in cell_source:
        cell_source = f"{cell_source}\n<updated></updated>"
        updated = True
    if not updated:
        print(f"{fp.name} unchanged")
        return

    cell["source"] = cell_source
    nb["cells"][0] = cell
    nbformat.write(nb, fp, 4)
    print(f"Saved {fp.name}")


if __name__ == "__main__":
    folder = Path(__file__).parent.parent / "mynotes" / "notes"
    nb = find_notebooks(folder)
    for n in nb:
        add_tags(n)
