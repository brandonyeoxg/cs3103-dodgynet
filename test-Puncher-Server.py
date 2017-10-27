import queue
from Puncher import PuncherProtocol
import Config
p = PuncherProtocol(**Config.puncher)
p.server.start()
