# WebGUI Demo
from webgui import init,send,ask,addev,rmev,type,data,security # Basic WebGUI imports

btnevnum = None
async def run(ws): # On connection to client
    await send(ws, { # Select the button
        type: "select",
        data: "button#test",
    })
    global btnevnum
    btnevnum = await addev(ws, "click", btnclick) # Add callback event listener
    await send(ws, { # Show alert
        type: "alert",
        data: "Try clicking the button!",
    })
    print("Default button font size:", await ask(ws, { # Get button style (font size)
        type: "getstyle",
        data: "fontSize",
    }))
    await send(ws, { # Set button style (font size)
        type: "setstyle",
        data: "fontSize=50px",
    })
async def btnclick(ws): # Callback event listener - Runs when the button is clicked
    print("Button clicked!")
    await rmev(btnevnum) # Remove callback event listener
    await send(ws, { # Show alert
        type: "alert",
        data: "Check the server log!",
    })
    await send(ws, { # Disable button
        type: "setattr",
        data: "disabled=true",
    })
    await send(ws, { # Set button style (background color)
        type: "setstyle",
        data: "backgroundColor=gray",
    })
init(run, "demo.html", keepopen = True) # Display HTML page
