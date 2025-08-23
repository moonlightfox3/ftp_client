from os import system # Used to open a browser window
import pathlib # Used to more easily get the current directory path
import asyncio # Async/await
from websockets.asyncio.server import serve # WebSocket server
import json # Used for encoding/decoding JSON messages

type = "type" # Makes typing out dictionary messages slightly faster, and more similar to JS
data = "data" # Same as above
security = "security" # Same as above (is an optional dictionary key)

numclients = 0
async def handler(ws):
    try:
        async for message in ws:
            await decode(ws, message)
    except Exception as error:
        if not stop.done():
            stop.set_result(1)
        print("Stopping server due to error:", error)
async def decode(ws, message): # Message decoding
    raw = json.loads(message)
    type = raw["type"]
    data = raw["data"]
    global numclients
    if type == "init": # Client connect
        numclients = numclients + 1
        print("Client connected: " + data + " (" + str(numclients) + " total)")
        await _connectcallback(ws)
    elif type == "end": # Client disconnect
        numclients = numclients - 1
        print("Client disconnected: " + data + " (" + str(numclients) + " total)")
        if numclients <= 0:
            print("Stopping server")
            stop.set_result(0)
        else:
            print("Not all clients are disconnected (" + str(numclients) + " total)")

    elif type == "reselect": # Select more specific element, get possible selected element count
        pass
    elif type == "check": # Check if selected element exists
        pass
    
    elif type == "getval": # Get value of selected element
        pass
    elif type == "getattr": # Get attribute of selected element
        pass
    elif type == "getstyle": # Get style of selected element
        pass
    
    elif type == "addev": # Add event listener to selected element
        pass
    elif type == "runev": # Run callback event listener from element
        if data in evlist:
            await evlist[data](ws)

    elif type == "confirm": # Show confirmation prompt
        pass
    elif type == "prompt": # Show text prompt
        pass
    
    elif type == "eval": # Run code with eval
        pass
        
    else: # Unknown
        print("Received unknown: (" + type + ") " + str(data))
        return await send(ws, {
            "type": "unknown",
            "data": "command",
        })
    return raw

async def send(ws, obj): # Message sending
    await ws.send(json.dumps(obj))
    return obj
async def ask(ws, obj): # Message sending, and expecting a reply
    await send(ws, obj)
    output = await decode(ws, await ws.recv())
    if output[type] != obj[type]:
        print("Invalid ask object: " + output[type] + "," + obj[type])
        return None
    else:
        return output[data]
evlist = {}
async def addev(ws, name, callback): # Add callback event listener
    num = await ask(ws, {
        type: "addev",
        data: name,
    })
    evlist[num] = callback
    return num
async def rmev(num): # Remove callback event listener
    evlist.pop(num)

stop = None
async def main(): # Start server
    async with serve(handler, "localhost", 8765):
        global stop
        stop = asyncio.get_running_loop().create_future()
        await stop
    if _disconnectcallback != None:
        await _disconnectcallback()
    if _keepopen:
        input("Press Enter to exit: ") # Keep terminal open

_connectcallback = None # Callback to run on a client connection
_keepopen = None # Keep the terminal open
_disconnectcallback = None # Callback to run when all clients disconnect
def init(connectcallback, htmlpath, keepopen = False, disconnectcallback = None): # Open GUI
    localpath = str(pathlib.Path(__file__).parent.resolve()) # Get current directory path
    print("Opening client")
    system('start ' + localpath + '\\' + htmlpath) # Opens the HTML file in (hopefully) the default browser
    print("Starting server")

    global _connectcallback
    _connectcallback = connectcallback
    global _keepopen
    _keepopen = keepopen
    global _disconnectcallback
    _disconnectcallback = disconnectcallback
    asyncio.run(main()) # Start server
if __name__ == "__main__":
    print("This script is intended to be imported.")
    input("Press Enter to exit: ") # Keep terminal open
    # USAGE:
    # Python:
    #from webgui import init,send,ask,addev,rmev,type,data,security # Basic WebGUI imports
    #
    #async def run(ws): # On connection to client
    #    pass
    #init(run, "<file name and path>.html", keepopen = True) # Display HTML page (replace "<file name and path>")
    #
    # Html:
    #<script src="./webgui.js"></script> <!-- Include WebGUI -->
