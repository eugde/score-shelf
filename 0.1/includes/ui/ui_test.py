from PyQt5.QtCore import QAbstractTableModel

__author__ = 'eugde'

import sys
from PyQt5 import QtWidgets, uic


class MyDialog(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi("data/stacked.ui", self)
        widget1 = self.ui.page
        widget2 = self.ui.page_2
        widget1.ui = uic.loadUi("data/widget1.ui", widget1)
        widget2.ui = uic.loadUi("data/widget2.ui", widget2)

        widget1.ui.button_1.clicked.connect(lambda x: self.ui.stackedWidget.setCurrentIndex(1))
        widget2.ui.button_2.clicked.connect(lambda x: self.ui.stackedWidget.setCurrentIndex(0))

app = QtWidgets.QApplication(sys.argv)
dialog = MyDialog()
dialog.show()
sys.exit(app.exec_())