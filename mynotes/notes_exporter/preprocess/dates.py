import re

from dateutil.parser import parse
from nbconvert.preprocessors import Preprocessor


class NBDateProcessorPP(Preprocessor):
    CREATED_SEARCH = re.compile(r"(?<=<created>)(.+?)(?=</created>)")
    UPDATED_SEARCH = re.compile(r"(?<=<updated>).+?(?=</updated>)")

    def preprocess(self, nb, resources):
        target_cell = next((cell for cell in nb.cells if cell.cell_type == "markdown"))
        created_result = self.CREATED_SEARCH.search(target_cell.source)
        updated_result = self.UPDATED_SEARCH.search(target_cell.source)
        if created_result:
            created_dt = parse(created_result.group().strip())
            resources["mynotes"]["created"] = created_dt
            target_cell.source = self.CREATED_SEARCH.sub(
                f"\n*Created: {created_dt.strftime('%Y-%m-%d')}*", target_cell.source
            )
            target_cell.source = re.sub("(</?created>)", "", target_cell.source)

        if updated_result:
            updated_dt = parse(updated_result.group().strip())
            resources["mynotes"]["updated"] = updated_dt
            target_cell.source = self.UPDATED_SEARCH.sub(
                f"\n*Updated: {updated_dt.strftime('%Y-%m-%d')}*", target_cell.source
            )
            target_cell.source = re.sub("(</?updated>)", "", target_cell.source)
        return nb, resources
