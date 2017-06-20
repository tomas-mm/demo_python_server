import re
import urllib2
from views import LoginView, ScoreView, HighestScoreView


class Urls(object):
    """
    Match url patterns and get the right view handler
    """
    def __init__(self):
        urls = [
            ('^/(?P<user_id>\d+)/login/?$', LoginView),
            ('^/(?P<level_id>\d+)/score/?$', ScoreView),
            ('^/(?P<level_id>\d+)/highscorelist/?$', HighestScoreView)
        ]

        self.urls = [(re.compile(r), c) for r, c in urls]

    def match(self, url):
        """
        If a valid url is found, it returns an initialized view, else None
        """
        parsed = urllib2.urlparse.urlparse(url)

        for regex, klass in self.urls:
            res = regex.match(parsed.path)
            if res:
                kwargs = res.groupdict()
                kwargs['query_params'] = urllib2.urlparse.parse_qs(parsed.query)
                return klass(**kwargs)

        return None
