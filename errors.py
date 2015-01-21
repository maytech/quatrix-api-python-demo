class AuthorizationError(BaseException):
    pass


class RequestError(BaseException):
    def __init__(self, resource, status_code, response_text):
        self.resource = resource
        self.status_code = status_code
        self.response_text = response_text