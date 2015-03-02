#!/usr/bin/env python3
from PyQt5.QtGui import  QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QListView
import sys
import ui_steamchat_webapi
import getpass
import steam_webapi
import datetime
import time

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

def format_message(to, timestamp, text):
    t = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "(" + t + ") " + to + ": " + text


class MainWindow(QMainWindow, ui_steamchat_webapi.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)


class ChatWindow(QMainWindow, ui_steamchat_webapi_chatwindow.Ui_chatWindow):
    def sendmessage(self, m):
        text = self.messageInput.text()
        message = format_message(self.contactname, int(time.time()), text)
        self.historyarea.append(message)
        self.messageInput.clear()
        print("send", message)
        #TODO: implement API

    def __init__(self, parent=None, contactname = "", contactid = ""):
        super(ChatWindow, self).__init__(parent)
        self.setupUi(self)
        self.friendnameLabel.setText(self.friendnameLabel.text() + contactname)
        self.setWindowTitle(self.windowTitle() + " - " + contactname)
        self.sendButton.clicked.connect(self.sendmessage)

        chatlog = steam_webapi.get_chatlog(contactid)
        for logentry in sorted(chatlog, key=lambda x: x["m_tsTimestamp"]):
            contact = logentry["m_unAccountID"]
            ts = logentry["m_tsTimestamp"]
            if contact in contacts:
                cn = contacts[contact]["m_strName"]
            else:
                cn = "unknown"
            message = format_message(cn, ts, logentry["m_strMessage"])
            self.historyarea.append(message)

        self.messageInput.setFocus()
        self.contactid = contactid
        self.contactname = cn


app = QApplication(sys.argv)
form = MainWindow()

lmodel = QStandardItemModel()
for k in contacts.keys():
    c = contacts[k]
    if "is_self" in c: continue # don't display ourselves
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
    chatwindow = ChatWindow(parent=form, contactname=d["m_strName"], contactid=str(d["m_unAccountID"]))
    chatwindow.show()
    #print("created chatwindow")

form.contactlist.doubleClicked.connect(create_chatwindow)

form.show()
sys.exit(app.exec_())