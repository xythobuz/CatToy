from wifi import Wifi
from config import Config
from toy import Toy
from log import LogDup
import random
import time
from machine import Timer
import os

stdio_data = LogDup()
os.dupterm(stdio_data)

print("Initializing CatToy...")
t = Toy()

max_laser_power = 0.1

limits = [
    # pan_min, pan_max, tilt_min, tilt_max, name
    (84, 120, 53, 76, '3d printer tower, top'),
    (84, 120, 53, 76, 'office desk, front right'),
    (t.maximum_limits[0], t.maximum_limits[1], t.maximum_limits[2], t.maximum_limits[3], 'maximum'),
]

minimumBatteryVoltage = 3.25 * 2.0
maximumBatteryVoltage = 4.2 * 2.0

timerRunning = False
timerData = None
outlineIndex = 0
buttonSelection = 0
ledPattern = None
patternIndex = 0
patternTime = time.ticks_ms()
buttonTime = None

repeatTimer = Timer()
buttonTimer = Timer()
ledTimer = Timer()

random.seed()

def buildPage(header, footer):
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
            <form action="/random_move" method="get">
                <input type="submit" name="s" value="Go to random position">
            </form>
            <h2>Auto Play</h2>
            <form action="/repeat" method="get">
                Limits:
                <select name="limit">
                    %s
                </select><br>
                Steps: <input type="text" name="steps" value="100"><br>
                Duration: <input type="text" name="duration" value="1000">ms<br>
                <input type="submit" name="s" value="Random">
                <input type="submit" name="s" value="Outline"><br>
                Status: %s
            </form>
            <h2>Status</h2>
            <p><b>Battery:</b> %s
            %s
            <h2>Console</h2>
            <pre>%s</pre>
        </body>
    </html>
    """

    sl = ""
    for pan_min, pan_max, tilt_min, tilt_max, name in limits:
        val = name.replace(' ', '_').replace(',', '').lower()
        sl += '<option value="' + val + '">' + name + '</option>'
    sl += '<option value="">None</option>'

    status = "No program running"
    if timerRunning:
        status = "Program in progress"

    vb = t.getBatteryVoltage()
    pb = (vb - minimumBatteryVoltage) / (maximumBatteryVoltage - minimumBatteryVoltage) * 100.0
    pb = max(min(pb, 100), 0)
    battery = str(vb) + "V (" + str(pb) + "%)"

    page = html % (header, int(max_laser_power * 100.0), sl, status, battery, footer, stdio_data.data.decode("utf-8"))
    return page

def rootCallback(request):
    pan_min, pan_max, tilt_min, tilt_max = t.maximum_limits
    return buildPage(
        '<p>Welcome to the Cat Toy interface by <a href="https://www.xythobuz.de">xythobuz</a>.</p>',
        "<p><b>Limits:</b> tMin={} tMax={} pMin={} pMax={}</p>".format(tilt_min, tilt_max, pan_min, pan_max)
    )

def servoCallback(request):
    if t.getBatteryVoltage() < minimumBatteryVoltage:
        stopRepeat()
        t.free()
        return buildPage(
            '<p>Error: Battery Voltage too low. <b>Please charge them!</b></p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    q = request.find("/servos?")
    p1 = request.find("s1=")
    p2 = request.find("s2=")
    if (q < 0) or (p1 < 0) or (p2 < 0):
        print("servo query error: q={} p1={} p2={}".format(q, p1, p2))
        return buildPage(
            '<p>Error: no servo arguments found in URL query string.</p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    servos = [p1, p2]
    result = []
    for p in servos:
        pe = request.find("&s", p)
        if (pe < 0) or (p + 3 >= pe) or (pe - (p + 3) > 3):
            pe = request.find(" HTTP", p)
        if (pe < 0) or (p + 3 >= pe) or (pe - (p + 3) > 3):
            print("servo query error: p={} pe={}".format(p, pe))
            return buildPage(
                '<p>Error parsing query string.</p>',
                '<p><a href="/">Back to main page</a></p>'
            )
        r = request[p + 3 : pe]
        s = int(r)
        result.append(s)

    print("servos: pan={} tilt={}", result[0], result[1])
    t.angle(t.pan, result[0])
    t.angle(t.tilt, result[1])

    return buildPage(
        '<p>Servos move to s1=' + str(result[0]) + ' s2=' + str(result[1]) + '.</p>',
        '<p><a href="/">Back to main page</a></p>'
    )

def laserCallback(request):
    if t.getBatteryVoltage() < minimumBatteryVoltage:
        stopRepeat()
        t.free()
        return buildPage(
            '<p>Error: Battery Voltage too low. <b>Please charge them!</b></p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    value = 0.0
    text = "off"

    if request.find("?s=") == 10:
        pe = request.find(" HTTP", 10)
        r = request[13 : pe]
        if r != "Off":
            value = int(r)
            text = "to " + str(r) + '%'

    print("laser: {}%".format(value))
    t.laser(value / 100.0)

    return buildPage(
        '<p>Laser turned ' + text + '!</p>',
        '<p><a href="/">Back to main page</a></p>'
    )

def randomMoveCallback(request):
    if t.getBatteryVoltage() < minimumBatteryVoltage:
        stopRepeat()
        t.free()
        return buildPage(
            '<p>Error: Battery Voltage too low. <b>Please charge them!</b></p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    tilt = random.randint(t.tilt_min, t.tilt_max)
    pan = random.randint(t.pan_min, t.pan_max)
    print("random: tilt={} pan={}".format(tilt, pan))
    t.angle(t.tilt, tilt)
    t.angle(t.pan, pan)
    return buildPage(
        '<p>Random move to pan={} tilt={}</p>'.format(pan, tilt),
        '<p><a href="/">Back to main page</a></p>'
    )

def doMove(pan_min, pan_max, tilt_min, tilt_max, dur):
    tilt = random.randint(tilt_min, tilt_max)
    pan = random.randint(pan_min, pan_max)
    print("random move: tilt={} pan={} duration={}".format(tilt, pan, dur))
    t.angle(t.tilt, tilt)
    t.angle(t.pan, pan)

def doOutline(pan_min, pan_max, tilt_min, tilt_max, dur):
    global outlineIndex
    points = [
        (pan_min, tilt_min),
        (pan_min, tilt_max),
        (pan_max, tilt_max),
        (pan_max, tilt_min)
    ]
    outlineIndex = (outlineIndex + 1) % 4
    pan, tilt = points[outlineIndex]
    print("outline move: tilt={} pan={} duration={}".format(tilt, pan, dur))
    t.angle(t.tilt, tilt)
    t.angle(t.pan, pan)

def timerCallback(unused):
    global timerRunning, timerData, repeatTimer

    if t.getBatteryVoltage() < minimumBatteryVoltage:
        print("Abort due to low battery voltage: " + str(t.getBatteryVoltage()))
        stopRepeat()
        t.free()
        return

    if not timerRunning:
        return

    pan_min, pan_max, tilt_min, tilt_max, steps, duration, outline = timerData

    dur = duration
    if not outline:
        if dur < 200:
            dur = random.randint(200, 2000)
        else:
            dur = random.randint(200, duration)
    else:
        if dur < 200:
            dur = 500

    if steps > 0:
        steps -= 1
        if not outline:
            doMove(pan_min, pan_max, tilt_min, tilt_max, dur)
        else:
            doOutline(pan_min, pan_max, tilt_min, tilt_max, dur)
        repeatTimer.init(period = dur, mode = Timer.ONE_SHOT, callback = timerCallback)
    else:
        timerRunning = False
        t.laser(0.0)

    timerData = (pan_min, pan_max, tilt_min, tilt_max, steps, duration, outline)

def startRepeat(pan_min, pan_max, tilt_min, tilt_max, steps, duration, outline):
    global timerRunning, timerData
    timerData = (pan_min, pan_max, tilt_min, tilt_max, steps, duration, outline)

    if not timerRunning:
        timerRunning = True
        t.laser(max_laser_power)
        timerCallback(None)

def stopRepeat():
    global timerRunning, timerData
    timerRunning = False
    t.laser(0.0)

def repeatCallback(request):
    if t.getBatteryVoltage() < minimumBatteryVoltage:
        stopRepeat()
        t.free()
        return buildPage(
            '<p>Error: Battery Voltage too low. <b>Please charge them!</b></p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    q = request.find("/repeat?")
    pl = request.find("limit=", q)
    ps = request.find("steps=", pl)
    pd = request.find("duration=", ps)
    pp = request.find("s=", pd)
    if (q < 0) or (pl < 0) or (ps < 0) or (pd < 0) or (pp < 0):
        print("repeat query error: q={} pl={} ps={} pd={} pp={}".format(q, pl, ps, pd, pp))
        return buildPage(
            '<p>Error: no repeat arguments found in URL query string.</p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    data = [("limit=", pl), ("steps=", ps), ("duration=", pd), ("s=", pp)]
    result = []
    for s, p in data:
        #print(p)
        pe = request.find("&", p)
        #print(pe)
        if (pe < 0) or (p + len(s) > pe) or (pe - (p + 3) > 40):
            pe = request.find(" HTTP", p)
            #print(pe)
        if (pe < 0) or (p + len(s) > pe) or (pe - (p + 3) > 40):
            print("repeat query error: p={} pe={}".format(p, pe))
            return buildPage(
                '<p>Error parsing query string.</p>',
                '<p><a href="/">Back to main page</a></p>'
            )
        r = request[p + len(s) : pe]
        result.append(r)
        #print()

    print("repeat: limit={} steps={} duration={} s={}".format(result[0], result[1], result[2], result[3]))

    if len(result[0]) == 0:
        stopRepeat()
        return buildPage(
            '<p>Stopped repeated automatic moves!</p>',
            '<p><a href="/">Back to main page</a></p>'
        )

    outline = False
    if result[3].lower() == "outline":
        outline = True

    for pan_min, pan_max, tilt_min, tilt_max, name in limits:
        val = name.replace(' ', '_').replace(',', '').lower()
        if result[0] == val:
            startRepeat(pan_min, pan_max, tilt_min, tilt_max, int(result[1]), int(result[2]), outline)
            break

    return buildPage(
        '<p>Starting moves with limit={} steps={} duration={}</p>'.format(result[0], result[1], result[2]),
        '<p><a href="/">Back to main page</a></p>'
    )

def buttonCallback(state):
    global timerRunning, buttonSelection, buttonTime

    if state:
        buttonTime = time.ticks_ms()
    elif buttonTime != None:
        if time.ticks_diff(time.ticks_ms(), buttonTime) <= 500:
            buttonSelection = (buttonSelection + 1) % len(limits)
            print("Selection: " + str(buttonSelection + 1))
        else:
            if not timerRunning:
                pan_min, pan_max, tilt_min, tilt_max, name = limits[buttonSelection]
                print("Start pattern " + name)
                startRepeat(pan_min, pan_max, tilt_min, tilt_max, 200, 2500, False)
            else:
                print("Stop")
                stopRepeat()

def ledStatus():
    global timerRunning, buttonSelection, ledPattern, patternIndex, patternTime
    patternMode = False

    if t.getBatteryVoltage() < minimumBatteryVoltage:
        patternMode = True
        pattern = [ 100, 100 ]
    elif timerRunning:
        t.status(True)
    else:
        patternMode = True
        pattern = [ 300 ] * (buttonSelection * 2 + 1) + [ 1500 ]

    if patternMode:
        if pattern != ledPattern:
            ledPattern = pattern
            patternIndex = 0
            patternTime = time.ticks_ms()

        if time.ticks_diff(time.ticks_ms(), patternTime) >= ledPattern[patternIndex]:
            t.status(patternIndex % 2 == 1)
            patternIndex = (patternIndex + 1) % len(ledPattern)
            patternTime = time.ticks_ms()

def buttonTimerCallback(timer):
    global buttonTimer
    t.poll(buttonCallback)
    buttonTimer.init(period = 25, mode = Timer.ONE_SHOT, callback = buttonTimerCallback)

def ledTimerCallback(timer):
    global ledTimer
    ledStatus()
    ledTimer.init(period = 100, mode = Timer.ONE_SHOT, callback = ledTimerCallback)

print("Starting Timers...")
buttonTimerCallback(None)
ledTimerCallback(None)

print("Initializing WiFi...")
w = Wifi(Config.ssid, Config.password)
w.add_handler("/", rootCallback)
w.add_handler("/servos", servoCallback)
w.add_handler("/laser", laserCallback)
w.add_handler("/random_move", randomMoveCallback)
w.add_handler("/repeat", repeatCallback)
w.listen()

print("Ready!")
