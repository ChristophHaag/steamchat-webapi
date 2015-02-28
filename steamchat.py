#!/usr/bin/env python3
from PyQt5.QtGui import  QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication
import sys
import ui_steamchat_webapi
import getpass
import steam_webapi

#TODO: gui
my_username = input("Enter username: ")
my_password = getpass.getpass("Enter password: ") #input("Enter password: ").strip()

steam_webapi.login(my_username, my_password)

resp = steam_webapi.get_contactlist()
contacts = {}
for contact in resp:
    contacts[contact["m_unAccountID"]] = contact


class MainWindow(QMainWindow, ui_steamchat_webapi.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

app = QApplication(sys.argv)
form = MainWindow()

lmodel = QStandardItemModel()
for c in contacts.values():
    s = ""
    if "m_strName" in c and c["m_strName"]:
        s += c["m_strName"]
    else:
        s += c["m_unAccountID"]
    if "m_strInGameName" in c and c["m_strInGameName"]:
        s += " (in game: " + c["m_strInGameName"] + ")"
    item = QStandardItem()
    item.setText(s)
    item.setData(c)
    lmodel.appendRow(item)

form.contactlist.setModel(lmodel)

form.show()
sys.exit(app.exec_())