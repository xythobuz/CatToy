from wifi import Wifi
from config import Config
from toy import Toy

max_laser_power = 0.25

html = """<!DOCTYPE html>
<html>
    <head>
        <title>Cat Toy</title>
    </head>
    <body>
        <h1>Cat Toy</h1>
        %s
        <h2>Laser Pointer</h2>
        <form action="/laser" method="get">
            Turn power:
            <input type="range" name="s" min="0" max="100" step="1" value="%d">
            <input type="submit" value="Set"><br>
        </form>
        <form action="/laser" method="get">
            Or just turn it:
            <input type="submit" name="s" value="Off">
        </form>
        <h2>Pan and Tilt Servos</h2>
        <form action="/servos" method="get">
            Pan: <input type="text" name="s1"><br>
            Tilt: <input type="text" name="s2"><br>
            <input type="submit" value="Move">
        </form>
        %s
    </body>
</html>
"""

t = Toy()

def rootCallback(request):
    return html % (
        '<p>Welcome to the Cat Toy interface by <a href="https://www.xythobuz.de">xythobuz</a>.</p>',
        round(max_laser_power * 100.0),
        ''
    )

def servoCallback(request):
    q = request.find("/servos?")
    p1 = request.find("s1=")
    p2 = request.find("s2=")
    if (q < 0) or (p1 < 0) or (p2 < 0):
        return html % (
            '<p>Error: no servo arguments found in URL query string.</p>',
            round(max_laser_power * 100.0),
            '<p><a href="/">Back to main page</a></p>'
        )

    servos = [p1, p2]
    result = []
    for p in servos:
        pe = request.find("&s", p)
        if (pe < 0) or (p + 3 >= pe) or (pe - (p + 3) > 3):
            pe = request.find(" HTTP", p)
        if (pe < 0) or (p + 3 >= pe) or (pe - (p + 3) > 3):
            return html % (
                '<p>Error parsing query string.</p>',
            round(max_laser_power * 100.0),
                '<p><a href="/">Back to main page</a></p>'
            )
        r = request[p + 3 : pe]
        s = int(r)
        result.append(s)

    if result[0] < t.pan_min:
        result[0] = t.pan_min
    if result[0] > t.pan_max:
        result[0] = t.pan_max
    t.angle(t.pan, result[0])

    if result[1] < t.tilt_min:
        result[1] = t.tilt_min
    if result[1] > t.tilt_max:
        result[1] = t.tilt_max
    t.angle(t.tilt, result[1])

    return html % (
        '<p>Servos move to s1=' + str(result[0]) + ' s2=' + str(result[1]) + '.</p>',
        round(max_laser_power * 100.0),
        '<p><a href="/">Back to main page</a></p>'
    )

def laserCallback(request):
    value = 0.0
    text = "off"

    if request.find("?s=") == 10:
        pe = request.find(" HTTP", 10)
        r = request[13 : pe]
        if r != "Off":
            value = int(r)
            text = "to " + str(r) + '%'

    t.laser(value / 100.0)
    return html % (
        '<p>Laser turned ' + text + '!</p>',
        round(max_laser_power * 100.0),
        '<p><a href="/">Back to main page</a></p>'
    )

w = Wifi(Config.ssid, Config.password)
w.add_handler("/", rootCallback)
w.add_handler("/servos", servoCallback)
w.add_handler("/laser", laserCallback)
w.listen()
