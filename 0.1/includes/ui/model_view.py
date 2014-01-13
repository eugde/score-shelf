from PyQt5 import QtCore, QtWidgets, uic
import db_interface


class Model(QtCore.QAbstractTableModel):
    def __init__(self):
        super(Model, self).__init__()
        self.data = []
        self.columns = []

    def update(self, data_input):
        self.data = data_input
        print("Data updated!")
        print(self.data)

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.data)

    def columnCount(self,parent = QtCore.QModelIndex):
        return max([x for x in map(len, self.data)])

    def data(self, index, role=QtCore.Qt.DisplayRole):
        return self.data[index.row()][index.column()]


class View(QtWidgets.QTableView):
    def __init__(self,parent=None):
        super(View, self).__init__(parent)
        self.delegate = Delegate()
        self.setItemDelegate(self.delegate)


class Delegate(QtWidgets.QItemDelegate):
    def __init__(self, parent=None):
        super(Delegate, self).__init__(parent)

if __name__=="__main__":
    from sys import argv, exit


    class Widget(QtWidgets.QMainWindow):
        """
        A simple test widget to contain and own the model and table.
        """
        def __init__(self, parent=None):
            db = db_interface.DbHandler("test.db")
            data = db.fetch_table("test", ["name", "link_guitar"])
            print(data)

            QtWidgets.QMainWindow.__init__(self, parent)
            self.ui = uic.loadUi("data/table.ui", self)
            self._tm=Model()
            self._tm.update(data)
            self._tv=self.ui.testView
            self._tv.setModel(self._tm)




    a=QtWidgets.QApplication(argv)
    w=Widget()
    w.show()
    w.raise_()
    exit(a.exec_())