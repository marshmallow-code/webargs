import json
from aiohttp import web

def jsonify(data, **kwargs):
    kwargs.setdefault('content_type', 'application/json')
    return web.Response(
        body=json.dumps(data).encode('utf-8'),
        **kwargs
    )
