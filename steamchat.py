#!/usr/bin/env python3
from PyQt5.QtGui import  QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QListView
import sys
import ui_steamchat_webapi
import getpass
import steam_webapi

import ui_steamchat_webapi_chatwindow

#TODO: gui

contactlistreq = steam_webapi.get_contactlist() # maybe our session is still running
if not contactlistreq: # if not, log in and get the contact list again
    my_username = input("Enter username: ")
    my_password = getpass.getpass("Enter password: ") #input("Enter password: ").strip()
    steam_webapi.login(my_username, my_password)
    contactlistreq = steam_webapi.get_contactlist() # maybe our session is still running


contacts = {}
for contact in contactlistreq:
    contacts[contact["m_unAccountID"]] = contact
#print("Contacts:\n", contacts)


class MainWindow(QMainWindow, ui_steamchat_webapi.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)


class ChatWindow(QMainWindow, ui_steamchat_webapi_chatwindow.Ui_chatWindow):
    def sendmessage(self, m):
        text = self.messageInput.text()
        self.historyarea.append("me: " + text)
        self.messageInput.clear()
        print("send", text)
        #TODO: implement API

    def __init__(self, parent=None, contactname = ""):
        super(ChatWindow, self).__init__(parent)
        self.setupUi(self)
        self.friendnameLabel.setText(self.friendnameLabel.text() + contactname)
        self.setWindowTitle(self.windowTitle() + " - " + contactname)

        self.sendButton.clicked.connect(self.sendmessage)
        self.messageInput.setFocus()


app = QApplication(sys.argv)
form = MainWindow()

lmodel = QStandardItemModel()
for k in contacts.keys():
    c = contacts[k]
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
    item.setEditable(False)
    lmodel.appendRow(item)

form.contactlist.setModel(lmodel)

def create_chatwindow(itemindex):
    item = lmodel.itemFromIndex(itemindex)
    assert isinstance(item, QStandardItem)
    d = item.data()
    chatwindow = ChatWindow(parent=form, contactname=d["m_strName"])
    chatwindow.show()
    print("created chatwindow")

form.contactlist.doubleClicked.connect(create_chatwindow)

form.show()
sys.exit(app.exec_())