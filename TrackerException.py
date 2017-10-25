class TrackerException(Exception):
    mode = 'tracker'

    def __init__(self, message, data):
        self.message = message
        self.data = data

    def __repr__(self):
        return "<%s=>%s>%s:%s" % (self.__class__.__name__, self.mode, self.message, str(self.data))

class TrackerRequestException(TrackerException):
    mode = 'request'

class TrackerResponseException(TrackerException):
    mode = 'response'