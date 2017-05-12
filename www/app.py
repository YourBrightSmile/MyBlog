#coding=utf-8
import logging;logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web 

def index(request):
    return web.Response(body=b'<h1>xxxxxblog<h1>',content_type='text/html') 

#使用异步io的方式 初始化
async def init(loop):
    app=web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',8000)
    print('Server started at http://127.0.0.1:8000...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()