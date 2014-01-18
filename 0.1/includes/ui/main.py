from PyQt5 import QtCore, QtWidgets, QtGui, uic
import os, sys

import db_ui, db_interface

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = uic.loadUi(os.path.join("data", "main.ui"), self)

        self.ui.FilterLabel.setText("Test")
        self.entryTabs = db_ui.EntryTabView(parent = self.ui.entryFrame)
        self.ui.entryFrame.layout().addWidget(self.entryTabs, 10)
        self.entryTabs.set_entries([db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "")])])



if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("cleanlooks")

    mw = MainWindow(os.path.join("data", "main.ui"))

    mw.show()
    mw.raise_()

    sys.exit(app.exec_())