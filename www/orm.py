#coding=utf-8
import asyncio,aiomysql,logging

'''
    对常用的SELECT,INSERT,UPDATE,DELETE操作进行封装
'''
from sqlalchemy.sql.expression import except_

def log(sql,args=()):
    logging.info("SQL:%s",sql)
#异步方式创建连接池
async def create_pool(loop,**kw):
    logging.info('create database connection pool.....')
    #全局变量__pool存储连接池
    global __pool
    
    __pool = await aiomysql.create_pool(
        #从关键字参数中获取参数，设置一些默认值
        host=kw.get('host','localhost'),
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )
    
# 销毁连接池
async def destory_pool():
    global __pool
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()
        
        
#封装SELECT语句为一个函数
async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        #异步方式得到游标
        async with conn.cursor(aiomysql.DictCursor)as cur:
			#SQL语句的占位符是?,而MySQL的占位符是%s
			#注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击
            await cur.execute(sql.replace('?','%s'),args or ())
            if size:
            	rs = await cur.fetchmany(size)
            else:
            	rs = await cur.fetchall()  
        logging.info("rows returned :%s" % len(rs))    
        return rs
#封装Insert, Update, Delete为一个通用的函数
async def execute(sql,args,autocommit=True):
        log(sql)
        async with __pool.get() as conn:
            if not autocommit:
                await conn.begin()
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(sql.replace('?','%s'),args)
                    affectedRow=cur.rowcount
                    logging.debug('execute affectedRow'%affectedRow)
                if not autocommit:
                    await conn.commit()
                    
            except BaseException as e:
                if not autocommit:
                    await conn.rollback()
                raise 
            return affectedRow

#利用封装好的select和execute创建ORM 

#创建Field
class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)
class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)
class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)
class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)
#### 创建参数字符串'?,?,?...'
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)

#定义基类Model的元类 元类是类的模板，所以必须从type类型派生：
class ModelMetaclass(type):
    '''
        cls:当前准备创建类的对象 ，这里就是ModelMetaclass
        name:创建的类的名字
        bases:创建的类继承的父类集合
        attrs:创建的类的方法和属性集合（不包含其父类的属性和方法）
        __new__里面的内容在写一个类以这个元类为元类时的模块被执行时会执行，而不是在实例化的时候才执行

    '''
    def __new__(cls,name,bases,attrs):
        #排除对Model类的修改
        if name=='Model':
            return type.__new__(cls,name,bases,attrs)
        tableName=attrs.get('__table__',None) or name
        logging.info("found model :%s (table:%s)" %(name,tableName))
        mappings=dict()
        fields=[]
        primaryKey=None
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info("found mapping %s ===> %s " %(k,v))
                mappings[k]=v
                if v.primary_key:
                    #找到主键 如果已经有primaryKey表示有重复的主键
                    if primaryKey:
                        raise StandardError('Duplicate primary key for field :%s' %k)
                    primaryKey=k
                else:
                    fields.append(k)
        if not primaryKey:
            raise StandardError('Primary key not found.')
        #删除原有的属性和方法
        for k in mappings.keys():
            attrs.pop(k)
        #将原attrs中除去主键以外的其他的k变成 ['`k`',...]
        #myslq中的保留字不能用于字段名，比如desc: crate table desc会报错而crate table `desc`则不会
        #所以将表名，库名都加上反引号可以保证语句的执行度
        escaped_fields=list(map(lambda f: '`%s`' %f,fields))
        attrs['__mappings__'] = mappings #保存属性和列的映射关系
        attrs['__table__']  = tableName
        attrs['__primary_key__'] = primaryKey # 主键属性名
        attrs['__fields__'] = fields # 除主键外的属性名
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls,name,bases,attrs)
#定义所有ORM映射的基类Model  
class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)
    
    #为了使user['id']和user.id方式生效
    #当一个实例使用.调用不存在的属性时调用这个方法
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key) 
    def __setattr__(self, key, value):
        self[key] = value
    def getValue(self,key):
        #判断一个对象是否有某个属性，没用则返回设置的默认值，这里是None
        return getattr(self,key,None)
    
    def getValueOrDefault(self,key):
        value=getattr(self,key, None)
        if value is None:
            field=self.__mappings__[key]
            if field.default is not None:
                value=field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value
    @classmethod
    async def findAll(cls,where=None,args=None,**kw):
        'find object by where clause'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            slq.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        #print(sql,args)
        #返回的rs是一个元素是tuple的list 
        rs = await select(' '.join(sql),args)
        #cls类的列表 
        return [cls(**r) for r in rs]
    #findNumber() - 根据WHERE条件查找，但返回的是整数，适用于select count(*)类型的SQL
    @classmethod
    async def findNumber(cls,selectField,where=None,args=None,**kw):
        'find number by select and  where clause.'
        #select count(*) num from user;这样会将返回的结果那一列重命名为num
        sql = ['seclect %s _num_ from `%s`' % (selectField,cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']
    @classmethod
    async def find(cls, pk):
        ' find object by primary key. '
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
    
    async def save(self):
        #获取所有value
        logging.debug('model save ')
        args=list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        logging.debug('model save row : %s '%rows)
        if rows != 1:
            logging.warn("failed to insert recoder :affected rows :%s "% rows)
    async def update(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s' % rows)            

            
            
            
            
            
            
            
            
             