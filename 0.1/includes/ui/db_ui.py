#TODO: FIX HEADER
from PyQt5 import QtCore, QtWidgets, QtGui, uic
import os, sys
import math

import db_interface
import collection_interface, entry_dialog
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


class EntryTabView(QtWidgets.QTabWidget):
    def __init__(self, entries = None, widgets_per_page = 8, parent = None):
        """
        This TabWidget shows a collection of EntryView-Widgets on base of the entries passed to it.

        @param entries: A list of members of the Entry-class, containing the data to be displayed.
        """

        super(EntryTabView, self).__init__(parent)
        self.widgets_per_page = widgets_per_page
        self.pages_amount = 0
        self.set_entries(entries, widgets_per_page)
        self.setTabPosition(QtWidgets.QTabWidget.South)
        self.setTabShape(QtWidgets.QTabWidget.Triangular)



    def set_entries(self, entries, widgets_per_page = None):
        if not widgets_per_page:
            widgets_per_page = self.widgets_per_page

        if entries:
            self.pages_amount = math.ceil(len(entries)/widgets_per_page)
        self.clear()

        for page in range(0,self.pages_amount):
            self.addTab(EntryTabPage(entries[:(widgets_per_page-1)], parent = self), "Seite {}".format(page+1))
            entries = entries[widgets_per_page:]

        self.update()


class EntryTabPage(QtWidgets.QWidget):
    def __init__(self, entries, row_count = 2, col_count=4, parent = None):
        super(EntryTabPage,self).__init__(parent)

        self.setLayout(QtWidgets.QGridLayout(self))

        for row in range(0,row_count):
            for col in range(0, col_count):
                try:
                    widget = EntryView(entries[col], parent = self)
                    self.layout().addWidget(widget, row, col)
                except IndexError:
                    self.layout().addItem(QtWidgets.QSpacerItem(1,1,QtWidgets.QSizePolicy.Ignored),row,col)



class EntryView(QtWidgets.QWidget):
    def __init__(self, entry, db = db_interface.TrackDbHandler(constants.MAIN_DB_PATH), parent = None):
        super(EntryView, self).__init__(parent)

        self.entry = entry
        self.data = []

        self.db = db

        self.sizeRect = self.rect().adjusted(10,10, -10,-10)

        self.name = ""
        self.interpreter = ""
        self.thumbnail_location = ""
        self.thumbnail = QtGui.QImage()
        self.update_render_data()


        self.inFocus = False

        self.thumbnailRect = QtCore.QRect(0,0,self.thumbnail.width(), self.thumbnail.height())

    def update_entry(self):
        self.entry = self.db.get_entries(con_table = "tracks", con_col = "track_id",
                                         con_value = self.entry.get_track_id())
        self.update()

    def update_render_data(self):
        self.name = self.entry.data[1][1]
        self.interpreter = self.entry.data[2][1]
        self.thumbnail_location = self.entry.data[8][1]
        if os.path.isfile(self.thumbnail_location):
            self.thumbnail.load(self.thumbnail_location)
        else:
            self.thumbnail.load(os.path.join("data","img", "placeholder.png"))
            print()

    def enterEvent(self, event):
        self.inFocus = True
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.update()

    def leaveEvent(self, event):
        self.inFocus = False
        self.update()

    def mouseDoubleClickEvent(self, event):
        entryDialog = entry_dialog.EntryDialog(self.entry, parent = self)
        entryDialog.show()


    def paintEvent(self, event):
        self.sizeRect = self.rect().adjusted(10,10, -10,-10)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(255,255,255)))

        painter.drawRoundedRect(self.sizeRect.adjusted(-5,-5,10,10), 20,15)
        #TODO: Fix scaling!
        painter.drawImage(self.sizeRect, self.thumbnail, self.thumbnailRect)

        painter.drawText(self.sizeRect.adjusted(5,5,-10,-10), QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                            self.name+":\n"+self.interpreter)

        painter.save()
        if self.inFocus:
            painter.setOpacity(0.5)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(7,77,112)))
            painter.drawRoundedRect(self.sizeRect.adjusted(-5,-5,10,10), 20,15)
        painter.restore()


if __name__ == "__main__":
    print(os.path.abspath(__file__))
    print(os.path.abspath(__file__))
    app = QtWidgets.QApplication(sys.argv)
    db = db_interface.TrackDbHandler("data/test2.db")
    test_v = EntryTabView([db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                           db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")]),
                        ])
    test_v.set_entries([db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")])])
    test_v.resize(800,600)
    test_v.update()
    test_v.show()
    sys.exit(app.exec_())