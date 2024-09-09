from nbconvert.preprocessors import Preprocessor


class RemoveExecutionCountPP(Preprocessor):
    """Remove Execution Count"""

    def preprocess_cell(self, cell, resources, index):
        if cell.cell_type == "code" and "execution_count" in cell:
            cell.execution_count = None
        return cell, resources
