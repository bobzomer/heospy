
config_file = r'/home/pi/heos/heospy/config.json'

def get_current_album(player):
    res = player.cmd("player/get_now_playing_media", {})
    return '<html><head>%(album)s - %(artist)s</head><body><a href="http://www.deezer.com/album/%(album_id)s/"><h1>%(album)s - %(artist)s</h1><img src="%(image_url)s"/><br/>Album link</a></body></html>' % res['payload']

def play(player, url):
    res = player.cmd("browse/play_stream", {"url": url})
    return '<html><body>OK</body></html>'

def application(env, start_response):
    try:
        uri = env['REQUEST_URI'].split('?')
        heos_cmd = uri[0]
        heos_args = {}
        if len(uri) > 1:
            for a in uri[1].split('&'):
                key, val = a.split('=')
                heos_args[key] = val
        from heos_player import HeosPlayer
        import json
        if heos_cmd.startswith('/heos'):
            heos_cmd = heos_cmd[5:]
        else:
            start_response('200 OK', [('Content-Type','text/html')])
            return [bytes(str(env), encoding="utf8")]
        if heos_cmd.startswith('/'):
            heos_cmd = heos_cmd[1:]
        p = HeosPlayer(rediscover = False, config_file=config_file)
        if heos_cmd == 'get_current_album':
            res = get_current_album(p)
        elif heos_cmd == 'play':
            res = play(p, heos_args['url'])
        else:
            #res = json.dumps(p.cmd(heos_cmd, heos_args), indent=2)
            res = heos_cmd + str(heos_args)
        start_response('200 OK', [('Content-Type','text/html')])
        return [bytes(str(res), encoding="utf8")]
    except:
        start_response('200 OK', [('Content-Type','text/html')])
        import traceback
        return [bytes(traceback.format_exc(), encoding="utf8")]


