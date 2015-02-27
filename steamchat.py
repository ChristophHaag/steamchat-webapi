#!/usr/bin/env python3
from PyQt5.QtGui import  QStandardItemModel, QStandardItem

from PyQt5.QtWidgets import QMainWindow, QApplication
import sys
import ui_steamchat_webapi

import urllib.request
import urllib.parse
import json
import http.cookiejar
import os
import pickle

from xdg.BaseDirectory import xdg_data_home
cookiefile = xdg_data_home + "/.steamchatcookie"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/42.0.2305.3 Chrome/42.0.2305.3 Safari/537.36"
getrsa_url = "https://steamcommunity.com/login/getrsakey/"
login_url = "https://steamcommunity.com/login/dologin/"
captcha_url = "https://steamcommunity.com/public/captcha.php?gid="
chatlog_url = "https://steamcommunity.com/chat/chatlog/"

cj = http.cookiejar.CookieJar()
if (os.path.isfile(cookiefile)):
    with open(cookiefile, "rb") as f:
        cj._cookies = pickle.load(f)

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

my_username = input("Enter username: ").strip().encode("utf-8")

req = urllib.request.Request(
    getrsa_url,
    data=b"username=" + my_username,
    headers={
        'User-Agent': UA
    }
)

f = urllib.request.urlopen(req)
r = f.read()
resp = json.loads(r.decode('utf-8'))
#print(resp)
my_id = resp["steamid"]
friendstate_url = "https://steamcommunity.com/chat/friendstate/" + my_id

token_gid = resp["token_gid"] #TODO: what is this
timestamp = resp["timestamp"]

key_mod = resp["publickey_mod"]
key_exp = resp["publickey_exp"]

print("got rsa key")
#print("mod=" + key_mod)
#print("exp=" + key_exp)

import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
mod = int(key_mod, 16)
exp = int(key_exp, 16)
rsa_key = RSA.construct((mod, exp))
rsa = PKCS1_v1_5.PKCS115_Cipher(rsa_key)

import getpass
password = getpass.getpass() #input("Enter password: ").strip()

encrypted_password = rsa.encrypt(password.encode("utf-8"))
encrypted_password = base64.b64encode(encrypted_password)

#print("Encrypted password: " + encrypted_password.decode("utf-8"))

data =  b"username=" + my_username
data += b"&" + b"password=" + urllib.parse.quote_plus(encrypted_password).encode("utf-8")
data += b"&" +  b"rsatimestamp=" + timestamp.encode("utf-8")

captcha_req = False
guard_req = False

captchagid=-1
captchatext = ""
emailauth = ""
emailsteamid = ""

while True:
    if captcha_req:
        import os
        os.system("xdg-open " + captcha_url + captchagid + " >/dev/null 2>/dev/null")
        captchatext = urllib.parse.quote_plus(input("Captcha: " + captcha_url + captchagid + " > "))
    if guard_req:
        emailauth = urllib.parse.quote_plus(input("Guard Code > "))
    data2 =  b"&" + b"captchagid=" + str(captchagid).encode("utf-8")
    data2 += b"&" + b"captcha_text=" + captchatext.encode("utf-8")
    data2 += b"&" + b"emailauth="+ emailauth.encode("utf-8")
    data2 += b"&" + b"emailsteamid="+ emailsteamid.encode("utf-8")

    #print ((data+data2).decode("utf-8"))
    req = urllib.request.Request(
        login_url,
        data=data + data2,
        headers={
            'User-Agent': UA
        }
    )

    f = urllib.request.urlopen(req)
    resp = json.loads(f.read().decode('utf-8'))
    if "message" in resp and "Incorrect login" in  resp["message"]:
        print ("Incorrect login!")
        print(resp)
        exit()
    if "captcha_needed" in resp and resp["captcha_needed"]:
        captcha_req = True
        captchagid = resp["captcha_gid"]
    else:
        captcha_req = False
    if "emailauth_needed" in resp and resp["emailauth_needed"]:
        guard_req = True
        emailsteamid = resp["emailsteamid"]
    else:
        guard_req = False
    #print("Logged in:" + resp["message"])
    #print(resp)
    if not captcha_req and not guard_req:
        break
    #exit()

print("Logged in")
#print(cj._cookies)
with open(cookiefile, "wb") as f:
    pickle.dump(cj._cookies, f)

req = urllib.request.Request(
    "https://steamcommunity.com/chat",
    data=None,
    headers={
        'User-Agent': UA
    }
)
f = urllib.request.urlopen(req)
r = f.read().decode("utf-8")
#TODO: fix
right = (r.split("}, ["))[1]
middle = "[" + (right.split("], [] )"))[0] + "]"
#print(middle)
resp = json.loads(middle)
#print(resp)

contacts = {}
for contact in resp:
    contacts[contact["m_ulSteamID"]] = contact

print(contacts)

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
        s += c["m_ulSteamID"]
    if "m_strInGameName" in c and c["m_strInGameName"]:
        s += " (in game: " + c["m_strInGameName"] + ")"
    item = QStandardItem()
    item.setText(s)
    lmodel.appendRow(item)

form.contactlist.setModel(lmodel)

form.show()
sys.exit(app.exec_())