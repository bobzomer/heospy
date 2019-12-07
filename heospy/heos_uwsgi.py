import html
import traceback
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse, urlunparse, unquote_plus
from .heos_player import HeosPlayer


config_file = Path(__file__).absolute().parent.parent / 'config.json'


class AddCriteriaIds:
    PlayNow = 1
    PlayNext = 2
    AddToEnd = 3
    ReplaceAndPlay = 4


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
    url = unquote_plus(url)
    for u in url.split():
        if u.startswith('http'):
            url = html.unescape(u)
            break
    else:
        return '<html><body><h1>No URL found</h1>%s</body></html>' % url
    parsed_url = urlparse(url)
    cid = None
    mid = None
    if 'deezer' in parsed_url.netloc:
        *_, media_type, deezer_id = url.split('/')
        url = urlunparse(tuple(url)[:3]+('',)*3)
        sid = get_sources(player)['Deezer']['sid']
        if media_type == 'album':
            # browse/add_to_queue?pid=player_id&sid=source_id&cid=container_id&aid=add_criteria
            cid = 'Albums-%s' % deezer_id
        elif media_type == 'track':
            # browse/add_to_queue?pid=player_id&sid=source_id&cid=container_id&mid=media_id&aid=add-criteria
            mid = deezer_id
        else:
            return '<html><body><h1>Unsupported media type in URL</h1>%s</body></html>' % url
    else:
        return '<html><body><h1>Unsupported URL</h1>%s</body></html>' % url
    parameters = {"sid": sid, "aid": AddCriteriaIds.ReplaceAndPlay, "pid": player.pid}
    if cid is not None:
        parameters["cid"] = cid
    if mid is not None:
        parameters["mid"] = mid
    res = player.cmd("browse/add_to_queue", parameters)
    return '<html><body>%s</body></html>' % res['heos'] #['result']


def select_input_source(player, source):
    res = player.cmd('play_input', {"input": source})
    return '<html><body>%s</body></html>' % res['heos'] #['result']


@lru_cache(5)
def get_sources(player):
    res = player.cmd("browse/get_music_sources", {})
    return {src['name']: src for src in res['payload']}


def application(env, start_response):
    uri = None
    try:
        uri = env['REQUEST_URI'].split('?')
        heos_cmd = uri[0]
        heos_args = {}
        if len(uri) > 1:
            for a in uri[1].split('&'):
                try:
                    key, val = a.split('=')
                except ValueError:
                    key, val = 'url', a
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
        elif heos_cmd == 'get_sources':
            res = '<html><body><pre>%s</pre></body></html>' % html.escape(str(get_sources(p)))
        else:
            res = heos_cmd + str(heos_args)
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [bytes(str(res), encoding="utf8")]
    except:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [bytes('<b>Url:</b>%s<br/><pre>%s</pre>' %
                      (uri, html.escape(traceback.format_exc())), encoding="utf8")]


