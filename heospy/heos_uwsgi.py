import html
import traceback
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from .heos_player import HeosPlayer


config_file = Path(__file__).absolute().parent.parent / 'config.json'


def get_current_album(player):
    res = player.cmd("player/get_now_playing_media", {})
    return '''<html>
    <head><title>%(album)s - %(artist)s</title></head>
    <body>
        <a href="http://www.deezer.com/album/%(album_id)s/">
            <h1>%(album)s - %(artist)s</h1>
            <img src="%(image_url)s"/><br/>
            <h2>%(song)s</h2>
        </a>
    </body>
</html>''' % res['payload']


def play(player, url):
    for u in url.split():
        if u.startswith('http'):
            url = u
            break
    else:
        return '<html><body><h1>No URL found</h1>%s</body></html>' % url
    parsed_url = urlparse(url)
    if 'deezer' in parsed_url.netloc:
        url = urlunparse(tuple(url)[:3]+('',)*3)
    else:
        return '<html><body><h1>Unsupported URL</h1>%s</body></html>' % url
    res = player.cmd("browse/play_stream", {"url": url})
    return '<html><body>OK</body></html>'


@lru_cache(5)
def get_source(player):
    res = player.cmd("browse/get_music_sources", {})
    return {src['name']: src for src in res}


def application(env, start_response):
    uri = None
    try:
        uri = env['REQUEST_URI'].split('?')
        heos_cmd = uri[0]
        heos_args = {}
        if len(uri) > 1:
            for a in uri[1].split('&'):
                key, val = a.split('=')
                heos_args[key] = val
        if heos_cmd.startswith('/heos'):
            heos_cmd = heos_cmd[5:]
        else:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [bytes(str(env), encoding="utf8")]
        if heos_cmd.startswith('/'):
            heos_cmd = heos_cmd[1:]
        p = HeosPlayer(rediscover=False, config_file=str(config_file))
        if heos_cmd == 'get_current_album':
            res = get_current_album(p)
        elif heos_cmd == 'play':
            res = play(p, heos_args['url'])
        else:
            res = heos_cmd + str(heos_args)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [bytes(str(res), encoding="utf8")]
    except:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [bytes('<b>Url:</b>%s<br/><pre>%s</pre>' %
                      (uri, html.escape(traceback.format_exc())), encoding="utf8")]


