import orm,asyncio,sys
from models import User


loop = asyncio.get_event_loop()
async def test():
    await orm.create_pool(loop,user='www-data',password='www-data',db='GBlog')
    u=User(name='GG',email='xx@qq.com',password='1234')
    await u.save()
@asyncio.coroutine
def test():
    yield from orm.create_pool(loop,user='www-data',password='www-data',db='GBlog')
    u=User(name='test',email='xdx@qq.com',passwd='1234',image='about:blank')
	#u=User(name='test',email='test@test.com',passwd='1234',image='about:blank')
    yield from u.save()
    #yield from u.update()
    
	#a=yield from User.findAll()
    #b=yield from User.find(a[0].id)
    #print(b)
    #print(a)
    
    #rs=yield from User.findAll()
    #print(type(rs[0]))
    #yield from rs[0].remove()
    
loop.run_until_complete(test())
loop.close()
if loop.is_closed():
    sys.exit(0)