# Imports
import io
import json
import logging
import os
import signal
import sys
import time
import zipfile
from functools import wraps

from flask               import Flask, request, Response, render_template, abort, send_file, send_from_directory
from logging.handlers    import RotatingFileHandler
from tornado.httpserver  import HTTPServer
from tornado.ioloop      import IOLoop
from tornado.wsgi        import WSGIContainer
from werkzeug.exceptions import NotFound

run_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(run_path, ".."))

from etc.Settings      import Settings
from lib.DatabaseLayer import DatabaseLayer
from lib.Objects       import Song, Genre, Charter
from lib.TJA           import parse_tja, set_tja_metadata, clean_path

# Variables
conf = Settings()
app  = Flask(__name__, static_folder='static', static_url_path='/static')
db   = DatabaseLayer()

app.config['ASSETS'] = os.path.join(run_path, 'assets')

def archive(song, orig=True):
    tja  = db.tjas.get_tja(song)
    if not orig:
        tja = set_tja_metadata(tja, title=song.title_eng, sub=song.subtitle_eng,
                               song=clean_path(song.title_eng)+'.ogg')
    name = clean_path(song.title_orig) if orig else clean_path(song.title_eng)
    mov  = parse_tja(tja)['movie']
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "a", zipfile.ZIP_DEFLATED, False) as arch:
        arch.writestr(name+".tja", tja)
        arch.writestr(parse_tja(tja)['song'], db.tjas.get_ogg(song))
        arch.writestr(name+"_-_info.txt", db.tjas.get_info(song))
        if mov:
            arch.writestr(mov, db.tjas.get_mov(song))

    blob.seek(0)
    return (blob, name+'.zip')


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
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/api/browse', methods=['GET'])
def api_browse():
    data = db.songs.get_all()
    return api_reply(data)


@app.route('/browse', methods=['GET'])
def browse():
    data = api_browse()
    return render_template('browse.html', songlist=data)


@app.route('/download/orig/<id>', methods=['GET'])
def download_orig(id):
    try:
        song = db.songs.get_by_id(id)
        if song == None: abort(404)
        blob, name = archive(song, orig=True)
        return send_file(blob, mimetype="application/octet-stream",
                         as_attachment=True, download_name=name)
    except NotFound:
        abort(404)
    except Exception as e:
        print(e)
        abort(500)


@app.route('/download/eng/<id>', methods=['GET'])
def download_eng(id):
    try:
        song = db.songs.get_by_id(id)
        if song == None: abort(404)
        blob, name = archive(song, orig=False)
        return send_file(blob, mimetype="application/octet-stream",
                         as_attachment=True, download_name=name)
    except NotFound:
        abort(404)
    except Exception as e:
        print(e)
        abort(500)


@app.route('/custom/nameplates', methods=['GET'])
def custom_nameplates():
    return render_template('custom/nameplates.html')


@app.route('/custom/dons', methods=['GET'])
def custom_dons():
    return render_template('custom/dons.html')


@app.route('/custom/puchichara', methods=['GET'])
def custom_puchichara():
    return render_template('custom/puchichara.html')


@app.route('/assets/<asset>', methods=['GET'])
def assets(asset):
    try:
        return send_from_directory(app.config['ASSETS'], asset, as_attachment=True)
    except FileNotFoundError:
        abort(404)

###########
# Filters #
###########
@app.template_filter('number_format')
def number_format(number):
    if isinstance(number, type(None)):
        return ''
    if isinstance(number, str):
        try:
            number = float(number)
        except:
            return number
    if isinstance(number, int) and number == 0:
        return ''
    if isinstance(number, float) and number == int(number):
        number = int(number)
    return str(number)


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
