#coding=utf-8
import logging;logging.basicConfig(level=logging.DEBUG)
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web 
from glasses import priGlasses
from jinja2 import Environment,FileSystemLoader
import orm
from coroweb import add_routes,add_static
from handlers import cookie2user, COOKIE_NAME
IP = '192.168.155.1'
#初始化jinja2
def init_jinja2(app,**kw):
    logging.info('init jinja2 ........')
    options = dict(
        autoescape = kw.get('autoescape',True),
        block_start_string = kw.get('block_start_string','{%'),
        block_end_string = kw.get('block_end_string','%}'),
        variable_start_string = kw.get('variable_start_string','{{'),
        variable_end_string = kw.get('variable_end_string','}}'),
        auto_reload = kw.get('auto_reload',True)
    )
    path = kw.get('path',None)
    if path is None:
        #得到文件的目录名
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path:%s'%path)
    #加载 templates下的模板
    env = Environment(loader=FileSystemLoader(path),**options)
    filters = kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name]=f
    app['__templating__'] = env

#定义日志工厂函数    
async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request :%s %s'%(request.method,request.path))
        return (await handler(request))
    return logger
#定义数据工厂函数
async def data_factory(app,handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json:%s' %str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form :%s '%str(request.__data__))
            return (await handler(request))
    return parse_data
#定义响应工厂函数
async def response_factory(app,handler):
    async def response(request):
        logging.info('response_factory response...')
        
        r = await handler(request)
        logging.debug('response_factory response r:%s'%r)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)    
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        #default
        resp = web.Response(body=str(r).encode('utf_8'))
        resp.content_type='text/plain;charset=utf-8'
        logging.debug('response_factory response:%s'%resp)
        return resp
    return response

async def auth_factory(app, handler):
    async def auth(request):
        logging.info('check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
            if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
                return web.HTTPFound('/signin')
        return (await handler(request))
    return auth   
    
def datetime_filter(t):
    delta = int(time.time()-t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)




#使用异步io的方式 初始化
async def init(loop):
    priGlasses()
    await orm.create_pool(loop=loop,host='127.0.0.1',port=3306,user='www-data',password='www-data',db='gblog')
    app=web.Application(loop=loop,middlewares=[logger_factory,response_factory,auth_factory])
    add_routes(app,'handlers')
    add_static(app)
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    srv = await loop.create_server(app.make_handler(),IP,8000)
    logging.info('Server started at http://%s:8000...'%IP)
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
