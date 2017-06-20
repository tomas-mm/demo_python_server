# Demo server using BaseHttpServer module from Python 2.7

HTTP-based mini game back-end in Python which registers game scores for different users and levels, with the capability to return high score lists per level. There is also a simple login system in place (without any authentication...).

- No external framework is used (only integration and unit tests require requests and mock modules).
- Url matching and view definition are inspired by Django.
- The server may run on a multiprocess or multithread approach (see command help with `-h`).
- In both cases information is internally maintained and shared (there's no persistence in disk).

To get up and running simply: `python run_server.py`

To get more help:

    python run_server.py -h



    usage: run_server.py [-h] [-p PORT] [--host HOST] [--max_proc MAX_PROC]
                         [--threaded] [--logfile LOGFILE]
                         
    Game test server
    
    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  Port to listen to [default: 8080]
      --host HOST           Address to listen to [default: localhost]
      --max_proc MAX_PROC   Max children processes allowed (only for forked
                            server) [default: 60]
      --threaded            Use a multithread server (faster for non cpu intensive
                            tasks and low number of cores) instead of multiprocess
                            or forked (integration tests run in 45% of the time
                            used by multiprocess in a dual core i5 laptop)
      --logfile LOGFILE     Log file path [default: /tmp/basic_test_server.log]


## Run unit tests and integration tests
Integration tests automatically launch a server (both mutlithread and multiprocess) and send requests locally.
The runner runs both integration and unit tests.

    python test_runner.py
    
You may need to install requests and mock packages to run the tests:

    pip install -r requirements.txt

## Implemented functional requirements:

The functions are described in detail below and the notation <value> means a call parameter value or a return value. All calls shall result in the HTTP status code 200, unless when something goes wrong, where anything but 200 must be returned. Numbers parameters and return values are sent in decimal ASCII representation as expected (ie no binary format).
Users and levels are created “ad-hoc”, the first time they are referenced.

#### Login

This function returns a session key in the form of a string (without spaces or “strange” characters) which shall be valid for use with the other functions for 10 minutes. The session keys should be “reasonably unique”.

    Request: GET /<userid>/login
    Response: <sessionkey>
    <userid> : 31 bit unsigned integer number
    <sessionkey> : A string representing session (valid for 10 minutes). Example: http://localhost:8081/4711/login --> UICSNDK

#### Post a user's score to a level

This method can be called several times per user and level and does not return anything. Only requests with valid session keys shall be processed.

    Request: POST /<levelid>/score?sessionkey=<sessionkey>
    Request body: <score>
    Response: (nothing)
    <levelid> : 31 bit unsigned integer number
    <sessionkey> : A session key string retrieved from the login function. <score> : 31 bit unsigned integer number
     
    Example: POST http://localhost:8081/2/score?sessionkey=UICSNDK (with the post body: 1500)

#### Get a high score list for a level

Retrieves the high scores for a specific level. The result is a comma separated list in descending score order. Because of memory reasons no more than 15 scores are to be returned for each level. Only the highest score counts. ie: an user id can only appear at most once in the list. If a user hasn't submitted a score for the level, no score is present for that user. A request for a high score list of a level without any scores submitted shall be an empty string.
    
    Request: GET /<levelid>/highscorelist
    Response: CSV of <userid>=<score>
    <levelid> : 31 bit unsigned integer number
    <score> : 31 bit unsigned integer number
    <userid> : 31 bit unsigned integer number
    
    Example: http://localhost:8081/2/highscorelist - > 4711=1500,131=1220

