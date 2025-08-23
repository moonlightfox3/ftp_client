This is a (somewhat-) simple FTP client. It supports logging into an FTP server with a username and password, using an IP address and port. (However, as a warning - these details are sent over a normal WebSocket connection in plaintext.)

Requires the Python modules ftplib and websockets.
To use: Launch the Python script ftp_client.py. It will attempt to open the HTML file ftp_client_gui.html in a browser, but if your default application for HTML files is something else (like a text editor), you can open it yourself. The Python script will automatically exit when the HTMl page is closed, and the HTML page will close if the Python script is exited.

Supports: Listing items in the current directory and moving through directories (using the directory bar at the top of the page, or by clicking on folders), renaming and removing files and folders, and creating folders and uploading files. It does check (most) permissions for files and folders. (Also, if the FTP server responds with an error, the HTML page and Python script might close. To keep the Python script console window open after the HTML page closes, set ftp_client_debugmode to True instead of False in ftp_client.py.)

The webgui folder just contains the code for launching an HTML page and using it as a GUI for a Python script. The HTML page and Python script communicate through a WebSocket. This folder also has a simple demo for just this functionality, which is not required for this FTP client. webgui.py is intended to be imported into another Python script to be used, and will not do anything if launched by itself.
