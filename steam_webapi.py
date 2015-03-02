import json
import os
import pickle
import urllib.request
import http.cookiejar

from xdg.BaseDirectory import xdg_data_home
from xdg.BaseDirectory import xdg_config_home
cookiefile = xdg_data_home + "/.steamchatcookie"
configfile = xdg_config_home + "/.steamchat"
sessionid = None
my_id = None

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/42.0.2305.3 Chrome/42.0.2305.3 Safari/537.36"
getrsa_url = "https://steamcommunity.com/login/getrsakey/"
login_url = "https://steamcommunity.com/login/dologin/"
captcha_url = "https://steamcommunity.com/public/captcha.php?gid="
chatlog_url = "https://steamcommunity.com/chat/chatlog/"
friendstate_url = "https://steamcommunity.com/chat/friendstate/"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

# returns decoded response
# and sets session id
def http_request(url, data):
    global sessionid
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'User-Agent': UA
        }
    )
    f = urllib.request.urlopen(req)
    r = f.read().decode("utf-8")

    sid = getSessionIDfromCookies(cj) # perhaps we got a new sessionid, who knows
    if sid and not sid == sessionid:
        print("New sessionid: " + sid)
        sessionid = sid
    return r


def getSessionIDfromCookies(cookiejar):
    for cookie in cookiejar:
        if cookie.name == "sessionid":
            return cookie.value


def load_cookies(cookiefile):
    global sessionid
    if (os.path.isfile(cookiefile)):
        with open(cookiefile, "rb") as f:
            cj._cookies = pickle.load(f)
            sessionid = getSessionIDfromCookies(cj)


def store_cookies(cookiefile):
    with open(cookiefile, "wb") as f:
        pickle.dump(cj._cookies, f)


def encrypt_password(key_mod, key_exp, my_password):
    import base64
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    mod = int(key_mod, 16)
    exp = int(key_exp, 16)
    rsa_key = RSA.construct((mod, exp))
    rsa = PKCS1_v1_5.PKCS115_Cipher(rsa_key)

    encrypted_password = rsa.encrypt(my_password.encode("utf-8"))
    encrypted_password = base64.b64encode(encrypted_password)
    return encrypted_password

def receive_id():
    return json.loads(http_request(getrsa_url, b"username=" + my_username.encode("utf-8")))["steamid"]

def login(my_username, my_password):
    global my_id
    resp = json.loads(http_request(getrsa_url, b"username=" + my_username.encode("utf-8")))

    my_id = resp["steamid"]
    token_gid = resp["token_gid"] #TODO: what is this
    timestamp = resp["timestamp"]
    key_mod = resp["publickey_mod"]
    key_exp = resp["publickey_exp"]

    print("got rsa key, now encrypting password")

    encrypted_password = encrypt_password(key_mod, key_exp, my_password)

    captcha_req = False
    guard_req = False

    captchagid=-1
    captchatext = ""
    emailauth = ""
    emailsteamid = ""

    # data that doesn't change no matter whether we need a captcha or guard code
    data =  b"username=" + my_username.encode("utf-8")
    data += b"&" + b"password=" + urllib.parse.quote_plus(encrypted_password).encode("utf-8")
    data += b"&" +  b"rsatimestamp=" + timestamp.encode("utf-8")

    while True:
        if captcha_req:
            os.system("xdg-open " + captcha_url + captchagid + " >/dev/null 2>/dev/null")
            captchatext = urllib.parse.quote_plus(input("Enter Captcha Text from " + captcha_url + captchagid + " > "))
        if guard_req:
            emailauth = urllib.parse.quote_plus(input("Enter Guard Code from Email  "))

        # data that changes when we entered a captcha or guard code
        data2 =  b"&" + b"captchagid=" + str(captchagid).encode("utf-8")
        data2 += b"&" + b"captcha_text=" + captchatext.encode("utf-8")
        data2 += b"&" + b"emailauth="+ emailauth.encode("utf-8")
        data2 += b"&" + b"emailsteamid="+ emailsteamid.encode("utf-8")

        resp = json.loads(http_request(login_url,data + data2))

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

        if not captcha_req and not guard_req:
            print("Successfully Logged in") #TODO: check possible errors
            store_cookies(cookiefile)
            break


def get_chatlog(m_unAccountID):
    # whe the fuck do we need the send the sessionid in a POST request when it is already in the cookie?
    # steam web responds with a 403 if we don't....
    data = b"sessionid=" + urllib.parse.quote_plus(sessionid).encode("utf-8")
    r = http_request(chatlog_url + m_unAccountID, data)
    return json.loads(r)

def get_contactlist():
    r = http_request("https://steamcommunity.com/chat", None)
    #TODO: fix
    try:
        right = (r.split("}, ["))[1]
        middle = "[" + (right.split("], [] )"))[0] + "]"
        contacts = json.loads(middle)

        right = r.split("WebAPI, ")[1]
        middle = right.split(", [{")[0] #TODO empty list
        myself = json.loads(middle)
        myself["is_self"] = True

        contacts.append(myself)
        return contacts
    except:
        return None

load_cookies(cookiefile)

