import threading
import multiprocessing
import logging
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ForkingMixIn, ThreadingMixIn
from responses import *
from urls import Urls


logger = logging.getLogger('handler')


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    url_patterns = Urls()

    def handle_in_view(self, command, data):
        proc = multiprocessing.current_process()
        thread = threading.currentThread()
        logger.debug('Process: %s pid=%s, thread: %s, method: %s', proc.name, proc.ident, thread.getName(), self.command)

        try:
            view = self.url_patterns.match(self.path)
            if not view:
                response = ResponseNotFound()
            else:
                response = getattr(view, command)(self.headers, data)
        except Exception as e:
            logger.error('Error processing view: %s', e, exc_info=True)
            response = ResponseInternalServerError()

        self.send_response(response.code)

        self.send_header('Content-Length', len(response.data))
        if ('Content-Type' not in response.headers and
            'content-type' not in response.headers):
            self.send_header('Content-Type', 'text/plain')
        for k, v in response.headers.iteritems():
            self.send_header(k, v)
        self.end_headers()

        logger.debug('response data: < %s >', response.data)
        if response.data:
            self.wfile.write(response.data)
        self.wfile.write('\n')

    def do_GET(self):
        self.handle_in_view('get', None)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))  # already supports lower case header
        data = self.rfile.read(content_length)
        self.handle_in_view('post', data)

    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))  # already supports lower case header
        data = self.rfile.read(content_length)
        self.handle_in_view('put', data)

    def do_HEAD(self):
        self.handle_in_view('head', None)

    def do_DELETE(self):
        self.handle_in_view('delete', None)


class ForkedHTTPServer(ForkingMixIn, HTTPServer):
    """Handle requests in a separate process."""
    timeout = 30
    active_children = None
    max_children = 60

    def set_max_children(self, max_children):
        self.max_children = max_children


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread"""

    def set_max_children(self, max_children):
        pass


def server_factory(settings):
    if settings.threaded:
        server = ThreadedHTTPServer((settings.host, settings.port), Handler)
    else:
        server = ForkedHTTPServer((settings.host, settings.port), Handler)

    return server


