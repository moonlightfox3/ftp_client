from webgui.webgui import init,send,ask,addev,rmev,type,data,security # Basic WebGUI imports
from ftplib import FTP
from io import BytesIO
import json

ftp_client_debugmode = False
if ftp_client_debugmode:
    print("FTP client is in debug mode!")

async def run(ws): # On WebGUI connection
    await addev(ws, None, connect_ev)
async def stoprun(): # On WebGUI disconnection
    if connected:
        print("Disconnecting from FTP server...")
        closeftp()
        print("Disconnected from FTP server.")
async def connect_ev(ws):
    ip = await get_el_val(ws, "#ipInp", "value")
    port = await get_el_val(ws, "#portInp", "value")
    user = await get_el_val(ws, "#userInp", "value")
    passwd = await get_el_val(ws, "#passwdInp", "value")
    if connect(ip, port, user, passwd):
        await rmev(0)
        await send(ws, {
            type: "select",
            data: "span#welcomeMsg",
        })
        await send(ws, {
            type: "setval",
            data: "innerText=" + msg_rmcode(ftp.getwelcome()),
        })
        await ask(ws, {
            type: "eval",
            data: "onConnect()",
        })
        await sendcwd(ws)

        await addev(ws, None, closeftp_ev)
        await addev(ws, None, setcwd_ev)
        await addev(ws, None, movecwd_ev)
        await addev(ws, None, rnitem_ev)
        await addev(ws, None, rmitem_ev)
        await addev(ws, None, mkfolder_ev)
        await addev(ws, None, getfile_ev)
        await addev(ws, None, putfile_ev)
    else:
        await ask(ws, {
            type: "eval",
            data: "onConnectFail()",
        })
async def get_el_val(ws, selector, val):
    await send(ws, {
        type: "select",
        data: selector,
    })
    return await ask(ws, {
        type: "getval",
        data: val,
        security: "resplogdatarm",
    })

ftp = None
connected = False
cwd = "/"
def connect(ip="127.0.0.1", port="5000", user="anonymous", passwd=""):
    global ftp
    global connected
    if connected:
        print("Already connected to FTP server")
        return False
    print("Connecting to FTP server...")
    try:
        if ftp == None:
            ftp = FTP()
        ftp.connect(ip, int(port))
        ftp.login(user, passwd)
        connected = True
        print("Connected to FTP server!")
        return True
    except:
        ftp = None
        print("Failed to connect to FTP server.")
        return False

def msg_fmtcode(msg):
    return "(" + msg[0:3] + ") " + msg[4:]
def msg_rmcode(msg):
    return msg[4:]

def listitems():
    itemsraw = ftp.mlsd(cwd, ["size", "type", "perm"])
        # size   : Size in bytes - can be an estimation
        # type   : Entry type (file, cdir - current dir, pdir - parent dir, dir)
        # perm   : Permissions (a - (file) can append content to, c - (dir) can create files in, d - (all) can delete, e - (dir) can enter, f - (all) can rename, l - (dir) can list contents of, m - (dir) can create dirs in, p - (dir) can delete items in, r - (file) can read contents of, w - (file) can write contents of)
    items = []
    for item in itemsraw: # itemsraw is a generator that outputs tuples, this conversion makes the output simpler to serialize into JSON and send.
        items.append([item[0], item[1]])
    return items
def movecwd(path):
    global cwd
    if cwd == "/":
        outcwd = "/" + path
    else:
        outcwd = cwd + "/" + path
    ftp.cwd(outcwd)
    cwd = outcwd
def setcwd(newcwd):
    global cwd
    ftp.cwd(newcwd)
    cwd = newcwd
def getcwd():
    return ftp.pwd()
def mkfolder(name):
    ftp.mkd(name)
def rmfolder(name):
    global cwd
    maincwd = cwd
    movecwd(name)

    _rmfolderrun()
    setcwd(maincwd)
    ftp.rmd(name)
def _rmfolderrun():
    global cwd
    items = listitems()
    for item in items:
        if item[1][type] == "file":
            rmfile(item[0])
        elif item[1][type] == "dir":
            origcwd = cwd
            movecwd(item[0])
            _rmfolderrun()
            setcwd(origcwd)
            ftp.rmd(item[0])
def rnitem(oldname, newname):
    ftp.rename(oldname, newname)
def rmfile(name):
    ftp.delete(name)
def getfile(name):
    global _getfilecontent
    _getfilecontent = b""
    ftp.retrbinary("RETR " + name, _getfilerun)

    out = _getfilecontent
    _getfilecontent = None
    return out.hex()
_getfilecontent = None
def _getfilerun(data):
    global _getfilecontent
    _getfilecontent = _getfilecontent + data
def putfile(name, data):
    fp = BytesIO(bytes.fromhex(data))
    ftp.storbinary("STOR " + name, fp)
def quitfiletransfer():
    ftp.abort() # Might not always work
def closeftp():
    try:
        ftp.quit()
        return True
    except:
        return False
def forcecloseftp():
    try:
        ftp.close()
        return True
    except:
        return False

async def sendcwd(ws):
    await send(ws, {
        type: "select",
        data: "input#cwdInp",
    })
    await send(ws, {
        type: "setval",
        data: "value=" + getcwd(),
    })
    await senditems(ws)
async def senditems(ws):
    items = listitems()
    await ask(ws, {
        type: "eval",
        data: "showDirListing(`" + json.dumps(items) + "`)",
    })

async def getchangeditem(ws):
    await send(ws, {
        type: "select",
        data: "span.listItem.changeSend",
    })
    await send(ws, {
        type: "setval",
        data: "className=listItem",
    })
    return (await ask(ws, {
        type: "getval",
        data: "innerText",
    }))[4:]
async def closeftp_ev(ws):
    closeftp()
async def setcwd_ev(ws):
    await send(ws, {
        type: "select",
        data: "input#cwdInp",
    })
    try:
        setcwd(await ask(ws, {
            type: "getval",
            data: "value",
        }))
    except:
        await send(ws, {
            type: "alert",
            data: "That folder doesn't exist or you don't have permission to enter it.",
        })
    await sendcwd(ws)
async def movecwd_ev(ws):
    name = await getchangeditem(ws)
    movecwd(name)
    await sendcwd(ws)
async def rnitem_ev(ws):
    oldname = await getchangeditem(ws)
    newname = (await ask(ws, {
        type: "getval",
        data: "dataset",
    }))["newName"]
    rnitem(oldname, newname)
    await senditems(ws)
async def rmitem_ev(ws):
    name = await getchangeditem(ws)
    itemtype = (await ask(ws, {
        type: "getval",
        data: "dataset",
    }))["itemType"]
    if itemtype == "file":
        rmfile(name)
    elif itemtype == "dir":
        rmfolder(name)
    await senditems(ws)
async def mkfolder_ev(ws):
    name = await getchangeditem(ws)
    mkfolder(name)
    await senditems(ws)
async def getfile_ev(ws):
    name = await getchangeditem(ws)
    hex = getfile(name)
    await send(ws, {
        type: "runev",
        data: hex,
    })
async def putfile_ev(ws):
    name = await getchangeditem(ws)
    hexdata = (await ask(ws, {
        type: "getval",
        data: "dataset",
    }))["hexData"]
    putfile(name, hexdata)
    await senditems(ws)

init(run, "..\\ftp_client_gui.html", keepopen = ftp_client_debugmode, disconnectcallback = stoprun) # Display HTML page
