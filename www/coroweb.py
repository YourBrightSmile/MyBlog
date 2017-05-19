#coding=utf-8
'''
    inspect库
            可以帮助我们检查类的内容，检查方法的代码，提取和格式化方法的参数
'''

import asyncio,os,inspect,logging,functools
from urllib import  parse
from aiohttp import web
#from apis import APIError 
from flask import app



def get(path):
    '''
        Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='GET'
        wrapper.__route__=path
        return wrapper
    return decorator

def post(path):
    '''
        Define decorator @get('/path')
    '''
    def decorator(func):
        #使用后被修饰的方法的__name__不会发生改变
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='POST'
        wrapper.__route__=path
        return wrapper
    return decorator

#取出必须要给出的命名关键字参数，就是命名关键字参数中不包括指定了默认值的项
#比如def fun(a,b=0,*c,d,e=1,**f)
#这其中d和e就是必须的命名关键字参数，传入时必须指定参数名称
def get_required_kw_args(fn):
    args=[]
    #inspect.signature(fn)返回inspect.Signature类型对象里面包含fn函数的所有参数
    #inspect.signature(fn).parameters会将fn的所有参数变成一个OrderDict
    #OrderDict的key是按插入的顺序排序的
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        #param.kind就是参数类型有
        #POSITIONAL_OR_KEYWORD 位置参数或必选参数
        #VAR_POSITIONAL        可变参数
        #KEYWORD_ONLY          命名关键字参数
        #VAR_KEYWORD           关键字参数
        #按照这里的规则(a,b=0,*c,d,e=1,**f) 只能有d
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default==inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

#取出命名关键字参数
def get_named_kw_args(fn):
    args=[]
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        #按照这里的规则(a,b=0,*c,d,e=1,**f) 只能有d,e
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

#判断是否有命名关键字参数
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True
#判断是否有关键字参数
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


#判断是否有请求参数
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name,param in params.items():
        if name == 'request':
            found = True
            continue
        #如过有request参数，而且这个参数不是VAR_KEYWORD KEYWORD_ONLY VAR_POSITIONAL
        if found and (param.kind!=inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and parm.kind!=inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found
#处理request请求
class RequestHandler(object):
    def __init__(self,app,fn):
        self._app=app
        self._func=fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)
    async def __call__(self,request):
        logging.info('RequestHandler __call__ request:%s'%request)
        kw = None
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            #处理三种POST提交请求JSON,常规表单,文件上传
            if request.method =='POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Miss Content-Type')
                #请求类型
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object')
                    kw=params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    #fun(**d)表示把字典中的所有元素传进去
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type :%s'% request.content_type)
            #处理GET请求
            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw=dict()
                    for k,v in parse.parse_qs(qs,True).items():
                        kw[k]=v[0]
        if kw is None:
            kw =dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                #移除所有未命名的kw
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name]=kw[name]    
                kw=copy
            #检查命名参数
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args:%s'%k)
                kw[k]=v
        if self._has_request_arg:
                kw['request']=request
        #check required kw
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument:%s'%name)
        logging.info('call with args:%s'%str(kw))
        try:
            r = await self._func(**kw)
            logging.debug('RequestHandler try:%s'%r)
            return r
        except:
        #except APIError as e:
            #return dict(error=e.error,data=e.data,message=e.message)
            pass
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info('add static %s ===> %s'%('static',path))
def add_route(app,fn):
    method = getattr(fn, '__method__',None)
    path = getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError("@get or @post not defined in %s ."%str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)'%(method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    #将RequestHandler传入app
    app.router.add_route(method, path, RequestHandler(app, fn))
#利用add_route一次添加一个模块中的多个handler
def add_routes(app,module_name):
    #找到最后一个.的位置
    n = module_name.rfind('.')
    if n==(-1):
        #globals,locals(只读)两个函数主要提供，基于字典的访问局部和全局变量的方式
        mod = __import__(module_name,globals(),locals())
    else:
        name=module_name[n+1:]
        #__import__(modname,globals(),locals(),[name]) 从modname导入指定的name模块 
        #类似from .. import xxx 
        mod = getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn=getattr(mod,attr)
        if callable(fn):
            method = getattr(fn,'__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app,fn)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
