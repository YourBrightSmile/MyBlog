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
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
		Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
		Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
		Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
		Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
    ]
    user=await User.find("001494662207376e3fc945031af454e85a983371e51ab49000")

    return {
        '__template__' :'blogs.html',
        'blogs':blogs,
        'user':user,
        }
@get('/test')
async def test(request):
    user=await User.findAll()
    
    return {
        '__template__' :'test.html',
        'user':user,
        }