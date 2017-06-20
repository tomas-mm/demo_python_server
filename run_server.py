import sys
import threading
import multiprocessing
import logging
import logging.handlers
import argparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ForkingMixIn, ThreadingMixIn
from responses import *
from storage import init_storage
from urls import Urls


logger = logging.getLogger()


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


def get_parameters():
    parser = argparse.ArgumentParser(description='Game test server')
    parser.add_argument('-p', '--port', type=int,
                        default=8080,
                        help='Port to listen to [default: %(default)s]')

    parser.add_argument('--host', type=str,
                        default='localhost',
                        help='Address to listen to [default: %(default)s]')

    parser.add_argument('--max_proc', type=int,
                        default=60,
                        help=('Max children processes allowed (only for forked server) '
                              '[default: %(default)s]'))

    parser.add_argument('--threaded', action='store_true',
                        default=False,
                        help=("Use a multithread server (faster for non cpu intensive tasks and low number of cores) "
                              "instead of multiprocess or forked (integration tests run in 45%% of the time "
                              "used by multiprocess in a dual core i5 laptop)"))

    parser.add_argument('--logfile', type=str,
                        default='/tmp/basic_test_server.log',
                        help='Log file path [default: %(default)s]')

    return parser.parse_args()


def config_logger(logfile, debug=True):
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=2000000, backupCount=5)
    fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    if sys.stdin.isatty():
        # write also to stderr
        handler = logging.StreamHandler()
        fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        handler.setFormatter(fmt)
        logger.addHandler(handler)


def simple_server_main():
    args = get_parameters()

    config_logger(args.logfile)

    if args.threaded:
        init_storage(forked=False)
        server = ThreadedHTTPServer((args.host, args.port), Handler)
    else:
        init_storage(forked=True)
        server = ForkedHTTPServer((args.host, args.port), Handler)

    server.set_max_children(args.max_proc)
    logger.info('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


if __name__ == '__main__':
    simple_server_main()

