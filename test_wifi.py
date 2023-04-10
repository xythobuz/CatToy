from wifi import Wifi
from config import Config

w = Wifi(Config.ssid, Config.password)
w.listen()
