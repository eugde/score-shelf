#TODO: Make Widgets show
import os
import sys

from PyQt5 import QtCore, QtWidgets, QtGui, uic

import db_interface


class EntryDialog(QtWidgets.QDialog):
    def __init__(self, db, eid, cols = [], order=[], parent=None):
        super(EntryDialog, self).__init__(parent)
        self.ui = uic.loadUi(os.path.join("data", "dialog", "view_dialog.ui"), self)
        self.entry_id = eid
        self.db = db

        self.data = self.db.fetch_table("test", columns=cols, condition=[("id =", self.entry_id)], dict_output=True)
        self.ui_lines = []
        if cols:
            output_order = order or cols
            for col in output_order:
                self.ui_lines.append(DataLine(col, self.data[0][col]))
        else:
            for col in self.data[0]:
                self.ui_lines.append(DataLine(col, self.data[0][col]))

        #These loops are used to distribute the data among the two vertical layouts in the dialog by a ratio of 5-2.

        for x in range(0, int(len(self.ui_lines)*(5/7))):
            line = self.ui_lines[x]
            #self.ui.data_l.addRow(line.title, line.content)
            self.ui.data_l.addWidget(line.title, x, 0)
            self.ui.data_l.addWidget(line.content, x, 1)
            line.title.show()
            line.content.show()
            print(x)

        print(self.ui.data_l.count())

        i = 0
        for x in range(int(len(self.ui_lines)*(5/7)), len(self.ui_lines)):
            line = self.ui_lines[x]
            #self.ui.data_r.addRow(line.title, line.content)
            self.ui.data_r.addWidget(line.title, i, 0)
            self.ui.data_r.addWidget(line.content, i, 1)
            line.title.show()
            line.content.show()
            print(x)
            i += 1

        self.thumbnail = QtGui.QPixmap(os.path.join("data", "img", "placeholder.png"))
        width = self.ui.Image.width()
        height = self.ui.Image.height()
        self.ui.Image.setPixmap(self.thumbnail.scaled(width,height,QtCore.Qt.KeepAspectRatio))

        self.ui.choiceButtons.accepted.connect(self.save_data)
        self.ui.choiceButtons.rejected.connect(self.close)

    def save_data(self):
        data_tbs = []
        for line in self.ui_lines:
            data_tbs.append((line.col, line.get_content()))
        self.db.update_table("test", data_tbs, [("id =", self.entry_id)])
        self.close()




class DataLine:
    def __init__(self, title, content):
        self.col = title
        self.title = QtWidgets.QLabel("{}: ".format(title))
        self.content = QtWidgets.QLineEdit(str(content))

    def get_content(self):
        return self.content.toPlainText()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = EntryDialog(db_interface.DbHandler("test.db"),1)
    mw.resize(600,600)
    mw.show()
    mw.raise_()
    sys.exit(app.exec_())