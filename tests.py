import os
import time
import random
import subprocess
import threading
import unittest
import requests
import storage
from mock import patch
from storage import NUM_TOP_SCORES, UserToken


class TestUserToken(unittest.TestCase):
    def setUp(self):
        self.time = time.time()

    def test_get(self):
        token = UserToken.get(103)
        self.assertTrue(len(token) == 25)

    @patch.object(storage.time, 'time')
    def test_validate(self, time_mock):
        time_mock.return_value = 1497904135
        token = '6PQpulUtEeef+gAAAAAAZQ==\n'
        user_id = UserToken.validate(token, 60)
        self.assertEqual(user_id, 101)

    def test_validate_ok(self):
        user_id = 103
        token = UserToken.get(user_id)
        u_id = UserToken.validate(token, .1)
        self.assertEqual(u_id, user_id)

    @patch.object(storage.time, 'time')
    def test_validate_timeout(self, time_mock):
        user_id = 103
        time_mock.side_effect = [self.time, self.time + 500]
        token = UserToken.get(user_id)

        u_id = UserToken.validate(token, 300)
        self.assertEqual(u_id, None)


format_data = (
    "<html>"
    "<head>"
    "<title> %(code)s %(message)s </title>"
    "</head>"
    "<body>"
    "<h1> %(code)s %(message)s </h1>"
    "</body>"
    "</html>"
    )


class ErrorResponse_400(object):
    code = 400
    message = 'Bad Request'
    value = format_data % locals()


class ErrorResponse_401(object):
    code = 401
    message = 'Unauthorized'
    value = format_data % locals()


class ErrorResponse_405(object):
    code = 405
    message = 'Method Not Allowed'
    value = format_data % locals()


class IntegTestViews(unittest.TestCase):
    """
    integration tests, are launched with the actual server running
    """
    DEFAULT_PORT = '8080'

    @classmethod
    def setUpClass(cls):
        dir_name = os.path.dirname(__file__)
        server_main = os.path.join(dir_name, 'run_server.py')
        fnull = open(os.devnull, 'w')
        cls.server_proc = subprocess.Popen(['python', server_main, '-p', cls.DEFAULT_PORT],
                                           shell=False, stdout=fnull, stderr=subprocess.STDOUT)
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server_proc.terminate()
        # kill any zombi manager
        subprocess.call(
            """kill -9 `ps aux | grep run_server.py | awk '{printf $2 " "}'` 2>/dev/null""",
            shell=True)

    def login_request(self, user_id):
        host = 'localhost'
        port = self.DEFAULT_PORT
        url = 'http://%(host)s:%(port)s/%(user_id)s/login' % locals()
        res = requests.get(url)
        return res

    def get_url(self, user_id):
        host = 'localhost'
        port = self.DEFAULT_PORT
        return 'http://%(host)s:%(port)s/%(user_id)s/login' % locals()

    def save_score(self, session_key, level_id, score):
        host = 'localhost'
        port = self.DEFAULT_PORT
        url = 'http://%(host)s:%(port)s/%(level_id)s/score?sessionkey=%(session_key)s' % locals()
        res = requests.post(url, data=str(score))
        return res

    def get_high_scores(self, level_id):
        host = 'localhost'
        port = self.DEFAULT_PORT
        url = 'http://%(host)s:%(port)s/%(level_id)s/highscorelist' % locals()
        res = requests.get(url)
        return res

    def assert_error_resp(self, res, error_type):
        self.assertEqual(res.status_code, error_type.code)
        self.assertEqual(res.content, error_type.value)

    def test_login_ok(self):
        res = self.login_request(4711)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.content), 25)

    def test_login_ko(self):
        res = self.login_request(2 ** 32)
        self.assert_error_resp(res, ErrorResponse_400)

    def test_level_ok(self):
        res = self.login_request(4711)
        self.assertEquals(res.status_code, 200)
        session_key = res.content
        res = self.save_score(session_key, 2, 15000)
        self.assertEqual(res.status_code, 204)
        self.assertEqual(len(res.content), 0)

    def test_level_unauthorized(self):
        res = self.save_score('bad_session_key', 2, 25000)
        self.assert_error_resp(res, ErrorResponse_401)

    def test_level_bad_score(self):
        res = self.login_request(4711)
        self.assertEquals(res.status_code, 200)
        session_key = res.content
        res = self.save_score(session_key, 2, 2 ** 32)
        self.assert_error_resp(res, ErrorResponse_400)

    def test_level_bad_level(self):
        res = self.login_request(4711)
        self.assertEquals(res.status_code, 200)
        session_key = res.content
        res = self.save_score(session_key, 2 ** 32, 25000)
        self.assert_error_resp(res, ErrorResponse_400)

    def test_high_score_not_repeated_user(self):
        res = self.login_request(1000)
        session_key = res.content
        res = self.save_score(session_key, 100, 25000)
        res = self.save_score(session_key, 100, 35000)

        res = self.get_high_scores(100)
        self.assertEqual(res.content, '1000=35000')

    def test_high_score_ok(self):
        exp_res = []
        for user in range(101, 121 + NUM_TOP_SCORES):
            res = self.login_request(user)
            res = self.save_score(res.content, 10, user - 100)
            self.assertEquals(res.status_code, 204)
            exp_res.append('%s=%s' % (user, user - 100))

        exp_res.reverse()
        expected_res = ','.join(exp_res[:NUM_TOP_SCORES])
        res = self.get_high_scores(10)
        self.assertEquals(res.status_code, 200)
        self.assertEqual(res.content, expected_res)

    def async_login_and_save_score(self, user, level, score):
        res = self.login_request(user)
        self.save_score(res.content, level, score)

    def test_high_score_ok_async(self):
        threads = []
        users_and_scores = range(101, 121 + NUM_TOP_SCORES)
        random.shuffle(users_and_scores)
        for user in users_and_scores:
            th = threading.Thread(target=self.async_login_and_save_score, args=(user, 11, user - 100))
            threads.append(th)

        for th in threads:
            th.start()

        for th in threads:
            th.join(2)

        expected_res = ','.join(['%s=%s' % (120 + i, 20 + i) for i in range(NUM_TOP_SCORES, 0, -1)])
        res = self.get_high_scores(11)
        self.assertEquals(res.status_code, 200)
        self.assertEqual(res.content, expected_res)

    def test_high_score_bad_level(self):
        res = self.get_high_scores(2 ** 32)
        self.assert_error_resp(res, ErrorResponse_400)

    def test_high_score_empty_level(self):
        res = self.get_high_scores(11)
        self.assertEqual(res.content, '')

    def test_methods_not_defined(self):
        url = self.get_url(4711)
        res = requests.delete(url)
        self.assert_error_resp(res, ErrorResponse_405)

        res = requests.head(url)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.content, '')

        res = requests.post(url, data='anything')
        self.assert_error_resp(res, ErrorResponse_405)


class IntegTestViewsTh(IntegTestViews):
    @classmethod
    def setUpClass(cls):
        dir_name = os.path.dirname(__file__)
        server_main = os.path.join(dir_name, 'run_server.py')
        fnull = open(os.devnull, 'w')
        cls.server_proc = subprocess.Popen(['python', server_main, '-p', cls.DEFAULT_PORT, '--threaded'],
                                           shell=False, stdout=fnull, stderr=subprocess.STDOUT)
        time.sleep(0.3)


if __name__ == '__main__':
    unittest.main()
