__all__ = ['Response', 'ResponseBadRequest', 'ResponseInternalServerError', 'ResponseNoContent',
           'ResponseNotAllowed', 'ResponseNotFound', 'ResponseUnauthorized']


class Response(object):
    def __init__(self, code, headers, data):
        self.code = code
        self.headers = headers
        self.data = data


class _DefaultResponse(type):
    def __init__(cls, name, bases, dct):
        super(_DefaultResponse, cls).__init__(name, bases, dct)

        if 'data' not in dct:
            cls.data = (
                "<html>"
                "<head>"
                "<title> %(code)s %(message)s </title>"
                "</head>"
                "<body>"
                "<h1> %(code)s %(message)s </h1>"
                "</body>"
                "</html>"
            ) % dct

        def _init(self, headers=None):
            self.headers = {'Content-Type': 'text/html'}
            if headers:
                self.headers.update(headers)

        cls.__init__ = _init


class ResponseNoContent(Response):
    __metaclass__ = _DefaultResponse
    code = 204
    data = ''


class ResponseBadRequest(Response):
    __metaclass__ = _DefaultResponse
    code = 400
    message = 'Bad Request'


class ResponseUnauthorized(Response):
    __metaclass__ = _DefaultResponse
    code = 401
    message = 'Unauthorized'


class ResponseNotFound(Response):
    __metaclass__ = _DefaultResponse
    code = 404
    message = 'Not Found'


class ResponseNotAllowed(Response):
    __metaclass__ = _DefaultResponse
    code = 405
    message = 'Method Not Allowed'


class ResponseInternalServerError(Response):
    __metaclass__ = _DefaultResponse
    code = 500
    message = 'Internal Server Error'
