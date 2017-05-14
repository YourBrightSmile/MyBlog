#coding=utf-8
import re,time,json,logging,hashlib,base64,asyncio
from coroweb import get,post
from models import User,Comment,Blog,next_id
'''
    url handlers
'''
@get('/')
async def index(request):
    logging.info('handle index ...')
    users = await User.findAll()
    return {
        '__template__' :'test.html',
        'users':users
        }
@get('/addtest')
async def addTest(request):
    logging.info('addTest ...')
    u = User(name='test1',email='test1@test.com',passwd='1234',image='about:blank')
    await u.save()
    logging.info('addTest...end')
    del u
    return 'ok'