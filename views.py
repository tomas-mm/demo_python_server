from storage import singletons
from responses import *


class ValidationError(Exception):
    pass


def validate_int(int_str, bit_len):
    try:
        int_val = int(int_str)
    except ValueError:
        raise ValidationError()

    if 0 <= int_val < 2 ** bit_len:
        return int_val
    else:
        raise ValidationError()


class BaseView(object):
    """
    Base View to inherit from, allowed methods must be overridden
    """
    def _get_query_param(self, param_name, default=None):
        """ every query parameter is read as a list in the matcher """
        param = self.query_params.get(param_name,
                                      [default] if not isinstance(default, list) else default)
        if len(param) == 1:
            return param[0]

    def get(self, headers, data):
        return ResponseNotAllowed()

    def post(self, headers, data):
        return ResponseNotAllowed()

    def head(self, headers, data):
        return ResponseNotAllowed()

    def delete(self, headers, data):
        return ResponseNotAllowed()

    def put(self, headers, data):
        return ResponseNotAllowed()


class LoginView(BaseView):
    """
    View objects are created per request
    """
    def __init__(self, user_id, query_params):
        self.user_id = user_id
        self.query_params = query_params

    def get(self, headers, data):
        try:
            self.user_id = validate_int(self.user_id, 31)
        except ValidationError:
            return ResponseBadRequest()

        token = singletons['users'].login(self.user_id)
        return Response(200, {}, token)


class ScoreView(BaseView):
    def __init__(self, level_id, query_params):
        self.level_id = level_id
        self.query_params = query_params

    def post(self, headers, data):
        try:
            self.level_id = validate_int(self.level_id, 31)
        except ValidationError:
            return ResponseBadRequest()

        try:
            score = validate_int(data, 31)
        except ValidationError:
            return ResponseBadRequest()

        # every query param is read as a list
        session_key = self._get_query_param('sessionkey')
        user_id = singletons['users'].validate(session_key)
        if not user_id:
            return ResponseUnauthorized()

        singletons['levels'].save_score(user_id, self.level_id, score)
        return ResponseNoContent()


class HighestScoreView(BaseView):
    def __init__(self, level_id, query_params):
        self.level_id = level_id
        self.query_params = query_params

    def get(self, headers, data):
        try:
            self.level_id = validate_int(self.level_id, 31)
        except ValidationError:
            return ResponseBadRequest()

        # user_id (session) is not required

        # dump to a csv with format <userid>=<score>,<userid>=<score>...
        res = singletons['levels'].get_highest_scores(self.level_id)
        str_list = []
        for user, score in res:
            str_list.append('%s=%s' % (user, score))
        message = ','.join(str_list)

        return Response(200, {'Content-Type': 'text/csv'}, message)

