from docx import Document
from docx.shared import Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.shared import OxmlElement, qn
from docx.table import Table


class CachedTable(Table):
    def __init__(self, tbl, parent):
        super(Table, self).__init__(parent)
        self._element = self._tbl = tbl
        self._cached_cells = None

    @property
    def _cells(self):
        if self._cached_cells is None:
            self._cached_cells = super(CachedTable, self)._cells
        return self._cached_cells

    @staticmethod
    def transform(table):
        cached_table = CachedTable(table._tbl, table._parent)
        return cached_table
