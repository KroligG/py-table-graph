from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

from util import to_float


class MyQtTable(QTableWidget):
    newTableDataEvent = QtCore.pyqtSignal(list)

    def __init__(self, *__args):
        super().__init__(*__args)
        self.setHorizontalHeaderLabels(['value'])
        self.cellClicked.connect(self.on_cell_click)
        self.itemChanged.connect(self.on_item_change)

    def on_item_change(self, QTableWidgetItem):
        self.newTableDataEvent.emit(self.get_table_data())

    def on_cell_click(self, row, col):
        if row == self.rowCount() - 1:
            self.insertRow(self.rowCount())

    def get_table_data(self):
        return [t for t in ((it[0], to_float(it[1].text())) for it in
                            ((i + 1, self.item(i, 0)) for i in range(0, self.rowCount())) if it[1]) if t[1]]

    def update_table(self, values: list):
        self.blockSignals(True)
        self.setRowCount(max(i[0] for i in values) + 1)
        for (i, x) in values:
            self.setItem(i - 1, 0, QTableWidgetItem(str(x)))
        self.blockSignals(False)
        self.newTableDataEvent.emit(self.get_table_data())
