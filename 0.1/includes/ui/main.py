from PyQt5 import QtCore, QtWidgets, QtGui, uic
import os, sys

#import db_ui, db_interface

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ui, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = uic.loadUi(ui, self)

        #Initializes the different pages of the stackedWidget and their UI.
        widget_1 = self.ui.stackedView.widget(0)
        widget_2 = self.ui.stackedView.widget(1)
        widget_1.ui = uic.loadUi(os.path.join("data", "subwidgets", "table_view.ui"), widget_1)
        widget_1.ui.tempButton.clicked.connect(lambda x: self.ui.stackedView.setCurrentIndex(1))
        widget_2.ui = uic.loadUi(os.path.join("data", "subwidgets", "placeholder.ui"), widget_2)

app = QtWidgets.QApplication(sys.argv)
app.setStyle("cleanlooks")

mw = MainWindow(os.path.join("data", "main.ui"))
mw.show()
mw.raise_()
sys.exit(app.exec_())