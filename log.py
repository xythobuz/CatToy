# https://forum.micropython.org/viewtopic.php?t=5442

import io

class LogDup(io.IOBase):
    def __init__(self):
        self.data = bytearray()

    def write(self, data):
        self.data += data
        if len(self.data) > 1024:
            self.data = self.data[len(self.data) - 1024 : ]
        return len(data)

    def readinto(self, data):
        return 0
