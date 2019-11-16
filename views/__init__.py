class WebPortalError(Exception):

    def __init__(self, message):
        super(WebPortalError, self).__init__(message)
        self.msg = message
