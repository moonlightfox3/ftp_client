class webgui { // Main WebGUI code
    static autoConnect = true // Automatically connect on page load
    static doDebugLogs = true // Enable debug console logs for activity
    static defaultIp = "127.0.0.1" // Default server IP
    static defaultPort = 8765 // Default server port (can be null)

    static ws = null // WebSocket
    static connect (ip = webgui.defaultIp, port = webgui.defaultPort) { // Connect to server
        if (webgui.ws != null) throw new Error("[webgui] Socket already connected")
        webgui.ws = new WebSocket(`ws://${ip}${port == null ? `` : `:${port}`}`)

        webgui.ws.onopen = function () { webgui.onConnect() }
        webgui.ws.onclose = function () { webgui.ws = null; webgui.onDisconnect() }
        webgui.ws.onerror = function () { webgui.onError() }
        webgui.ws.onmessage = function (ev) { webgui.onReceive(JSON.parse(ev.data)) }
    }
    static disconnect () { // Disconnect from server
        if (webgui.ws == null) throw new Error("[webgui] Socket not connected")
        webgui.ws.close()
        webgui.ws = null
    }

    static lastReceived = null // Last received message
    static selectedEl = document.body // Selected element, reference used in communication
    static possibleSelectedEls = [document.body] // Possible selected elements, reference used in communication
    static _nextSrvEv = 0 // Used for sending messages to the server on an event
    static onConnect () { // On connection to server
        if (webgui.doDebugLogs) console.debug("[webgui] Socket connected")
        webgui.sendData({
            type: "init",
            data: "Page opened",
        })
    }
    static onDisconnect () { // On disconnection from server
        if (webgui.doDebugLogs) console.debug("[webgui] Socket disconnected")
        close() // Don't keep open after disconnected
    }
    static onError () { // On error
        if (webgui.doDebugLogs) console.debug("[webgui] Socket error")
        throw "[webgui] Socket error"
    }
    static onReceive (obj) { // On message received
        let security = obj?.security?.split(",") ?? []
        let logObj = security.includes("logdatarm") ? "**hidden for security**" : obj
        if (webgui.doDebugLogs) console.debug("[webgui] Socket received:", logObj)
            
        webgui.lastReceived = obj
        if (!webgui._onReceive()) {
            let logData = security.includes("logdatarm") ? "**hidden for security**" : obj.data
            let hideResponseLog = security.includes("resplogdatarm")
            
            if (obj.type == "unknown") { // Unknown
                if (webgui.doDebugLogs) console.debug("[webgui] Socket sent unknown: " + logData)
            
            } else if (obj.type == "write") { // Write and replace document content
                if (webgui.doDebugLogs) console.debug("[webgui] Writing main content")
                document.body.innerHTML = obj.data
            
            } else if (obj.type == "select") { // Select element
                if (webgui.doDebugLogs) console.debug("[webgui] Selecting element: " + logData)
                webgui.possibleSelectedEls = [...document.querySelectorAll(obj.data)]
                webgui.selectedEl = webgui.possibleSelectedEls[0]
            } else if (obj.type == "reselect") { // Select more specific element, get possible selected element count
                if (webgui.doDebugLogs) console.debug("[webgui] Re-selecting element: " + logData)
                if (obj.data != null) webgui.selectedEl = webgui.possibleSelectedEls[obj.data]
                webgui.sendData({
                    type: "reselect",
                    data: webgui.possibleSelectedEls.length,
                })
            } else if (obj.type == "check") { // Check if selected element exists
                if (webgui.doDebugLogs) console.debug("[webgui] Checking exists: " + logData)
                let exists = webgui.selectedEl != null
                webgui.sendData({
                    type: "check",
                    data: exists,
                }, hideResponseLog)
            } else if (obj.type == "create") { // Create element inside selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Creating element: " + logData)
                let el = document.createElement(obj.data)
                webgui.selectedEl.append(el)
                webgui.possibleSelectedEls = [el]
                webgui.selectedEl = el
            } else if (obj.type == "remove") { // Remove selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Removing element: " + logData)
                webgui.selectedEl.remove()

            } else if (obj.type == "setval") { // Set value of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Setting value: " + logData)
                let [name, ..._val] = obj.data.split("="), val = _val.join("=")
                webgui.selectedEl[name] = val
            } else if (obj.type == "getval") { // Get value of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Getting value: " + logData)
                let val = webgui.selectedEl[obj.data]
                webgui.sendData({
                    type: "getval",
                    data: val,
                }, hideResponseLog)

            } else if (obj.type == "setattr") { // Set attribute of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Setting attribute: " + logData)
                let [name, ..._val] = obj.data.split("="), val = _val.join("=")
                webgui.selectedEl.setAttribute(name, val)
            } else if (obj.type == "getattr") { // Get attribute of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Getting attribute: " + logData)
                let val = webgui.selectedEl.getAttribute(obj.data)
                webgui.sendData({
                    type: "getattr",
                    data: val,
                }, hideResponseLog)

            } else if (obj.type == "setstyle") { // Set style of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Setting style: " + logData)
                let [name, ..._val] = obj.data.split("="), val = _val.join("=")
                webgui.selectedEl.style[name] = val
            } else if (obj.type == "getstyle") { // Get style of selected element
                if (webgui.doDebugLogs) console.debug("[webgui] Getting style: " + logData)
                let val = getComputedStyle(webgui.selectedEl)[obj.data]
                if (val === undefined) val = null
                webgui.sendData({
                    type: "getstyle",
                    data: val,
                }, hideResponseLog)

            } else if (obj.type == "addev") { // Add event listener
                if (webgui.doDebugLogs) console.debug("[webgui] Adding event listener")
                let evNum = null
                if (obj.data == null) { // Signal event listener
                    evNum = webgui._nextSrvEv; webgui._nextSrvEv++
                } else if (obj.data.indexOf("=") == -1) { // Callback event listener
                    evNum = webgui._nextSrvEv; webgui._nextSrvEv++
                    webgui.selectedEl.addEventListener(obj.data, () => webgui.sendData({
                        type: "runev",
                        data: evNum,
                    }, hideResponseLog))
                } else { // Event listener
                    let [name, ..._val] = obj.data.split("="), val = _val.join("=")
                    webgui.selectedEl.addEventListener(name, () => eval(val))
                }
                webgui.sendData({
                    type: "addev",
                    data: evNum,
                }, hideResponseLog)

            } else if (obj.type == "ctrl") { // Control selected element - focus, blur, click
                if (webgui.doDebugLogs) console.debug("[webgui] Controlling element: " + logData)
                if (obj.data == "focus") webgui.selectedEl.focus()
                else if (obj.data == "blur") webgui.selectedEl.blur()
                else if (obj.data == "click") webgui.selectedEl.click()

            } else if (obj.type == "alert") { // Show alert popup
                if (webgui.doDebugLogs) console.debug("[webgui] Showing alert")
                alert(obj.data)
            } else if (obj.type == "confirm") { // Show confirmation prompt
                if (webgui.doDebugLogs) console.debug("[webgui] Showing confirm")
                let val = confirm(obj.data)
                webgui.sendData({
                    type: "confirm",
                    data: val,
                }, hideResponseLog)
            } else if (obj.type == "prompt") { // Show text prompt
                if (webgui.doDebugLogs) console.debug("[webgui] Showing prompt")
                let val = prompt(obj.data)
                webgui.sendData({
                    type: "prompt",
                    data: val,
                }, hideResponseLog)

            } else if (obj.type == "eval") { // Run code with eval
                if (webgui.doDebugLogs) console.debug("[webgui] Running code with eval")
                let result = eval(obj.data)
                if (result === undefined) result = null
                webgui.sendData({
                    type: "eval",
                    data: result,
                })
            } else { // Unknown
                if (webgui.doDebugLogs) console.debug("Received unknown: (" + obj.type + ") " + logData)
            }
        }
    }
    static _onReceive = () => {} // Used when expecting a reply

    static sendData (obj, hideLog = false) { // Send message
        if (webgui.ws == null) throw new Error("[webgui] Not connected")
        if (webgui.doDebugLogs) console.debug("[webgui] Socket sent:", hideLog ? "**hidden for security**" : obj)
        
        let json = JSON.stringify(obj)
        webgui.ws.send(json)
        return obj
    }
    static async askData (obj, hideLog = false) { // Send message, expect reply
        if (webgui.ws == null) throw new Error("[webgui] Not connected")
        return new Promise(function (resolve) {
            webgui._onReceive = function () {
                if (webgui.lastReceived.type != obj.type) {
                    console.debug("[webgui] Invalid ask object: " + webgui.lastReceived.type + "," + obj.type)
                    resolve(null)
                } else resolve(webgui.lastReceived.data)

                webgui._onReceive = () => {}
                return true
            }
            webgui.sendData(obj, hideLog)
        })
    }
    static async askWaitData (obj, hideLog = false) { // Send message, expect reply, allow other communication
        if (webgui.ws == null) throw new Error("[webgui] Not connected")
        return new Promise(function (resolve) {
            webgui._onReceive = function () {
                if (webgui.lastReceived.type != obj.type) {
                    console.debug("[webgui] Unrelated ask object: " + webgui.lastReceived.type + "," + obj.type)
                    return false
                } else {
                    resolve(webgui.lastReceived.data)
                    webgui._onReceive = () => {}
                    return true
                }
            }
            webgui.sendData(obj, hideLog)
        })
    }
}
addEventListener("load", function () { // Auto-connect to server
    if (webgui.autoConnect) webgui.connect()
})
addEventListener("beforeunload", function () { // Auto-disconnect from server
    if (webgui.ws != null) {
        webgui.sendData({
            type: "end",
            data: "Page closed",
        })
        webgui.disconnect()
    }
    close() // Don't allow reloading, it disconnects from the server
})
