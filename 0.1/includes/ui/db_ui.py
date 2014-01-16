#TODO: FIX HEADER
from PyQt5 import QtCore, QtWidgets, QtGui
import os, sys

import db_interface
import collection_interface
from misc import helper_functions, constants


class DbModel(QtCore.QAbstractTableModel):
    def __init__(self, db, parent=None):
        super(DbModel, self).__init__(parent)
        self.data = []
        self.columns = []
        self.visible_columns = []
        self.db = db
        self.fetch_data("test")

    def fetch_data(self, table_name, columns = [], condition = [], condition_operator = "AND", dict_output = False):
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

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled


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


class CollectionModel(QtCore.QAbstractItemModel):
    def __init__(self, db, parent = None):
        super(CollectionModel, self).__init__(parent)

        self.db = db
        self.root = TreeItem("Sammlungen")
        self.collections = []
        self.data = []
        self.get_all_collections()

    def get_all_collections(self):

        del self.data[:]
        sql = "SELECT collection_name FROM collections"
        with self.db.db_connection:
            self.db.cursor.execute(sql)
            for collection in self.db.cursor.fetchall():
                col_name = collection[0]
                col_handler = collection_interface.CollectionHandler(col_name, self.db)
                self.data.append([col_name, col_handler])
                self.root.add_child(TreeItem(col_name))

    def get_collection_members(self, parent, collection):
        col_handler = collection[1]
        groups = col_handler.update_groups()
        for group in groups:
            group_item = TreeItem(group)
            for entry in groups[group]:
                entry_item = TreeItem(entry)
                group_item.add_child(entry_item)
            parent.add_child(group_item)


class TreeItem:
    def __init__(self, name, parent = None):
        self.name = name
        self.children = []
        self.parent = parent

    def __del__(self):
        for child in self.children:
            del child

    def row(self):
        if self.parent:
            return self.parent.children.index(self.name)
        else:
            return 0

    def add_child(self, child):
        if self.children.append(child):
            child.parent = self
            return child

    def del_child(self, child_name):
        try:
            self.children.pop(self.children.index(child_name))
        except ValueError:
            return False

    def data(self):
        return self.name

    def row(self):
        if self.parent():
            return self.parent.children.index(self)

        return 0

    def columnCount(self):
        return 1



class CollectionView(QtWidgets.QTreeView):
    def __init__(self, db, parent = None):
        super(CollectionView, self).__init__(parent)

        self.db = db
        self.setModel(CollectionModel(db))


class EntryView(QtWidgets.QWidget):
    def __init__(self, entry, parent = None):
        super(EntryView, self).__init__(parent)

        self.entry = entry
        self.data = []

        self.sizeRect = QtCore.QRect(10,10, 100,100)

        self.name = ""
        self.interpreter = ""
        self.thumbnail_location = ""
        self.thumbnail = QtGui.QImage()
        self.update_render_data()

        self.thumbnailRect = QtCore.QRect(0,0,self.thumbnail.width(), self.thumbnail.height())


    def update_render_data(self):
        self.name = self.entry.data[1][1]
        self.interpreter = self.entry.data[2][1]
        self.thumbnail_location = self.entry.data[8][1]
        if os.path.isfile(self.thumbnail_location):
            self.thumbnail.load(self.thumbnail_location)
        else:
            self.thumbnail.load(os.path.join("data","img", "placeholder.png"))
            print()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(self.sizeRect, self.thumbnail, self.thumbnailRect)
        painter.drawText(self.sizeRect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, self.name+":\n"+self.interpreter)


if __name__ == "__main__":
    print(os.path.abspath(__file__))
    print(os.path.abspath(__file__))
    app = QtWidgets.QApplication(sys.argv)
    db = db_interface.TrackDbHandler("data/test2.db")
    test_v = EntryView(db_interface.Entry([1,"Test","Beidl","Boobies","asdf","asdf","adsf","asdf",os.path.join("data", "img", "add.png")]))
    test_v.resize(500,500)
    test_v.show()
    sys.exit(app.exec_())