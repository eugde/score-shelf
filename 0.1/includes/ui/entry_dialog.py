#TODO: Make Widgets show
import os
import sys

from PyQt5 import QtCore, QtWidgets, QtGui, uic

import db_interface, constants


class EntryDialog(QtWidgets.QDialog):
    def __init__(self, entry, db = db_interface.TrackDbHandler(constants.MAIN_DB_PATH), parent=None):
        super(EntryDialog, self).__init__(parent)
        self.ui = uic.loadUi(os.path.join("data", "dialog", "view_dialog.ui"), self)
        self.entry = entry
        self.entry_id = self.entry.get_track_id()
        self.db = db

        self.ui_lines = []
        for line in self.entry.data[1:]:
            self.ui_lines.append(DataLine(line[0], line[1]))


        #These loops are used to distribute the data among the two vertical layouts in the dialog by a ratio of 5-2.

        for x in range(0, int(len(self.ui_lines)*(5/7))):
            line = self.ui_lines[x]
            #self.ui.data_l.addRow(line.title, line.content)
            self.ui.data_l.addWidget(line.title, x, 0)
            self.ui.data_l.addWidget(line.content, x, 1)
            line.title.show()
            line.content.show()

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

        if os.path.isfile(entry.data[8][1]):
            self.thumbnail_path = entry.data[8][1]
        else:
            self.thumbnail_path = (os.path.join("data","img", "placeholder.png"))

        self.ui.imageLabel.setPixmap(QtGui.QPixmap(self.thumbnail_path))
        self.ui.choiceButtons.accepted.connect(self.save_data)
        self.ui.choiceButtons.rejected.connect(self.close)

    #TODO: Update this
    def save_data(self):
        data_tbs = [self.entry.get_track_id()]
        for line in self.ui_lines:
            data_tbs.append((line.get_content()))
        #self.db.update_table("test", data_tbs, [("id =", self.entry_id)])
        print(data_tbs)
        self.entry.save_data(self.db, data_tbs)
        self.parent().update_entry()
        self.close()

    def resizeEvent(self, event):
        print(self.width(), self.height())

    def sizeHint(self):
        return QtCore.QSize(700,400)


class DataLine:
    def __init__(self, title, content):
        self.col = title
        self.title = QtWidgets.QLabel("{}: ".format(title))
        self.content = QtWidgets.QLineEdit(str(content))

    def get_content(self):
        return self.content.text()


class ImageLabel(QtWidgets.QLabel):
    def __init__(self, parent = None):
        super(ImageLabel, self).__init__(parent = parent)
        self.pixMapRect = QtCore.QRect(0,0,200, 200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        #self.setScaledContents(True)


    def paintEvent(self, event):
        if self.pixmap():
            print(self.pixmap().scaled(self.pixMapRect.size()).size())
            self.setPixmap(self.pixmap().scaled(self.pixMapRect.size(), QtCore.Qt.KeepAspectRatio))
        super(ImageLabel,self).paintEvent(event)
        print("Label ",self.width(), self.height())

    def sizeHint(self):
        return self.pixMapRect.size()

    def heightForWidth(w):
        return w

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    print(QtGui.QImageReader().imageFormat("data/img/segovia.jpg"))

    mw = EntryDialog(db_interface.Entry([1,"Test","Hallo","Tschüss","asdf","asdf","adsf","asdf",os.path.join("data", "img", "segovia.jpg")]))
    mw.resize(500,500)
    mw.show()
    mw.raise_()
    mw.resize(200,200)
    sys.exit(app.exec_())