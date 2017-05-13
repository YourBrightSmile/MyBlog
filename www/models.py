#coding=utf-8

'''
    Models for user,blog,comment
'''
import time,uuid
from orm import Model,StringField,BooleanField,FloatField,TextField

#定义一个创建唯一用户id的函数
def next_id():
    #%015 表示保留15位，不足用0补齐
    #15 + 32 + 3 总共50位 
    return '%015d%s000' %(int(time.time()*1000),uuid.uuid4().hex)

#定义用户类
class User(Model):
    __table__='users'
    id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)
#博客   
class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)

#评论
class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    