#TODO: FIX HEADER
import os
import sys

from PyQt5 import QtCore, QtWidgets, QtGui

import db_interface
from misc import helper_functions, constants


class DbModel(QtCore.QAbstractTableModel):
    def __init__(self, db, parent=None):
        super(DbModel, self).__init__(parent)
        self.data = []
        self.columns = []
        self.visible_columns = []
        self.db = db
        self.fetch_data("test")

    def fetch_data(self, table_name = constants.DEFAULTTABLE, columns = [], condition = [], condition_operator = "AND", dict_output = False):
        self.data = self.db.fetch_table(table_name, columns, condition, condition_operator, dict_output)
        self.columns = self.db.fetch_table_description(table_name)

    def rowCount(self, parent = QtCore.QModelIndex()):
        if self.data:
            return len(self.data)
        else:
            return 0

    def columnCount(self, parent = QtCore.QModelIndex()):

        if self.data:
            return max([x for x in map(len, self.data)])
        else:
            return 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        return [self.data[index.row()][index.column()], self.columns[index.column()]]

    def headerData(self, col, orientation, role=QtCore.Qt.EditRole):
        if orientation == QtCore.Qt.Horizontal:
            return QtCore.QVariant(self.columns[col])

    def sort(self, col, sortOrder=QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.data = sorted(self.data, key=lambda row: helper_functions.nonesort(row[col]), reverse=sortOrder)
        self.modelReset.emit()


class DbDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        super(DbDelegate, self).__init__(parent)
        self.mainFont = QtGui.QFont("Helvetica", 12)

    def paint(self, painter, option, index):

        painter.save()

        painter.setFont(self.mainFont)
        data = index.data()
        try:
            painter.drawText(option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, data[0])
        except TypeError:
            painter.drawText(option.rect, QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter, str(data[0]))

        painter.restore()


class DbView(QtWidgets.QTableView):
    def __init__(self, parent=None, db_name="test.db"):
        super(DbView, self).__init__(parent)

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)

        self.delegate = DbDelegate()
        self.setItemDelegate(self.delegate)
        db = db_interface.DbHandler(db_name)
        self.setModel(DbModel(db))
        self.columns = self.model().columns

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.verticalHeader().setVisible(False)
        print(type(self.horizontalHeader()))


if __name__ == "__main__":
    print(os.path.abspath(__file__))
    print(os.path.abspath(__file__))
    app = QtWidgets.QApplication(sys.argv)
    test_v = DbView()
    test_v.resize(500,500)
    test_v.show()
    sys.exit(app.exec_())