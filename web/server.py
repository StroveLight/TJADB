# Imports
import json
import logging
import os
import signal
import sys
import time
from functools import wraps

from flask              import Flask, request, Response, render_template, abort
from logging.handlers   import RotatingFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop     import IOLoop
from tornado.wsgi       import WSGIContainer

run_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(run_path, ".."))

from etc.Settings      import Settings
from lib.DatabaseLayer import DatabaseLayer
from lib.Objects       import Song, Genre, Charter

# Variables
conf = Settings()
app  = Flask(__name__, static_folder='static', static_url_path='/static')
db   = DatabaseLayer()

def dictify(data):
    if isinstance(data,(list, tuple, set)):
        items = []
        for item in data:
            items.append(dictify(item))
        return items
    elif isinstance(data, dict):
        for key, val in data.items():
            data[key] = dictify(val)
    elif isinstance(data, (Song, Charter, Genre)):
        return data.to_dict()
    return data


def api_reply(data):
    try:
        data = dictify(data)
        if request.url_rule.rule.lower().startswith('/api/'):
            data = json.dumps(data)
            return Response(data, mimetype='application/json'), 200
        else:
            return data
    except Exception as e:
        return Response('{"Error": "%s"}'%e, mimetype='application/json'), 500


##################
# ROUTE HANDLERS #
##################
@app.route('/api/browse', methods=['GET'])
def api_browse():
    data = db.songs.get_all()
    return api_reply(data)


@app.route('/browse', methods=['GET'])
def browse():
    data = api_browse()
    return render_template('browse.html', songlist=data)

##################
# Error Messages #
##################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


########################
# Web Server Functions #
########################
# signal handlers
def sig_handler(sig, frame):
    print('Caught signal: %s' % sig)
    IOLoop.instance().add_callback(self.shutdown)

def shutdown(self):
    MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3
    print('Stopping http server')
    http_server.stop()

    print('Will shutdown in %s seconds ...' % MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = IOLoop.instance()
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            print('Shutdown')
    stop_loop()


if __name__ == '__main__':
    if conf.debug:
        # start debug flask server
        app.run(host=conf.host, port=conf.port, debug=True)
    else:
        # start asynchronous server using tornado wrapper for flask
        # ssl connection
        print("Server starting...")
        if conf.ssl:
            ssl_options = {"certfile": os.path.join(run_path, "../", conf.certfile),
                           "keyfile": os.path.join(run_path, "../", conf.keyfile)}
        else:
           ssl_options = None
        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT,  sig_handler)

        http_server = HTTPServer(WSGIContainer(app), ssl_options=ssl_options)
        http_server.bind(conf.port, address=conf.host)
        http_server.start(0)  # Forks multiple sub-processes
        IOLoop.instance().start()