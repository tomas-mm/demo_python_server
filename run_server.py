import sys
import logging
import logging.handlers
import argparse
from bootstrap import init_singletons, singletons

logger = logging.getLogger()


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

    parser.add_argument('--store_tokens', action='store_true',
                        default=False,
                        help=("Store the user tokens in memory (only one token is valid per user at any time) "
                              "if the tokens are not stored, they are only invalidated by expiration time"))

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

    init_singletons(args)

    server = singletons['server']
    server.set_max_children(args.max_proc)
    logger.info('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


if __name__ == '__main__':
    simple_server_main()

