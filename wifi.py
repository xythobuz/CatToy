import network
import socket
import time
from machine import Pin

class Wifi:
    html = """<!DOCTYPE html>
    <html>
        <head>
            <title>Pico W</title>
        </head>
        <body>
            <h1>%s</h1>
            <p>%s</p>
            <pre>%s</pre>
        </body>
    </html>
    """

    def __init__(self, ssid, password, port = 80):
        # Check if wifi details have been set
        if len(ssid) == 0 or len(password) == 0:
            raise RuntimeError('Please set wifi ssid and password in config.py')
            self.led.value(1)

        self.led = Pin("LED", Pin.OUT)

        # Start connection
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(ssid, password)

        # Wait for connect success or failure
        max_wait = 20
        error_count = 20
        while max_wait > 0:
            if self.wlan.status() >= 3:
                break
            elif self.wlan.status() < 0:
                self.wlan.connect(ssid, password)
                error_count -= 1
                if error_count <= 0:
                    break
            else:
                max_wait -= 1
            print('waiting for connection...')
            self.led.value(not self.led.value())
            time.sleep(0.5)

        # Handle connection error
        if self.wlan.status() != 3:
            raise RuntimeError('wifi connection failed %d' % self.wlan.status())
            self.led.value(1)

        print('connected')
        status = self.wlan.ifconfig()
        print('ip = ' + status[0])

        # Open socket to the server
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        self.sock.bind(addr)
        self.sock.listen(1)
        print('listening on', addr)

        self.handlers = []
        self.led.value(0)

    def add_handler(self, path, callback):
        for hp, hc in self.handlers:
            if hp == path:
                raise RuntimeError('path is already registered %s' % path)
                self.led.value(1)
        h = (path, callback)
        self.handlers.append(h)


    def listen_once(self):
        # Listen for connections
        try:
            cl, addr = self.sock.accept()
            print('client connected from', addr)

            request = cl.recv(1024).decode('utf-8')
            #print(request)

            response = ""
            found = False
            for path, callback in self.handlers:
                pos = request.find(path)
                if ((pos == 4) or (pos == 5)) and ((request[pos + len(path)] == ' ') or (request[pos + len(path)] == '?')):
                    found = True
                    response = callback(request)
                    break

            code = 200
            title = "OK"
            if not found:
                code = 404
                title = "Not Found"
                response = self.html % (str(code), title, request)
            elif len(response) == 0:
                code = 503
                title = "Internal Server Error"
                response = self.html % (str(code), title, request)

            cl.send('HTTP/1.0 ' + str(code) + ' ' + title + '\r\nContent-type: text/html\r\n\r\n')
            cl.send(response)
        except OSError as e:
            print(e)
        finally:
            cl.close()
            print('connection closed')

    def listen(self):
        while True:
            self.listen_once()
