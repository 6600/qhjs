from twisted.web import server, resource
from twisted.internet import reactor
import re
import json
import time
import base64
import random
import pymysql
import secrets


config = {
  "dataBase": {
    "server": "bj-cynosdbmysql-grp-kqvvbnw0.sql.tencentcdb.com",
    "port": 28556,
    "user": "ceshi",
    "password": "ceshi",
    "name": "QHealthier"
  }
}

# 过滤SQL
def badSQL(str):
  return not re.compile('^[0-9A-Za-z\u4e00-\u9fa5\.\-_]+$').findall(str)

def login(data):
  global config
  body = json.loads(data)
  sourceIp = ''
  if ('type' not in body or 'username' not in body or 'password' not in body):
    return json.dumps({"err": 1, "message": "参数不正确!"})
  type = body['type']
  username = body['username']
  password = body['password']
  if (badSQL(type) or badSQL(username)):
    return {"err": 999, "message": "非法访问!"}
  if username and password:
    # 打开数据库连接
    connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        # 执行sql语句，进行查询
        cursor.execute("select * from `user` where username = '%s' and password = '%s'" % (username, password))
        # 获取查询结果
        result = cursor.fetchone()
        #print(result)
        connection.commit()
        # 如果没有结果使用手机登录
        if (not result):
            cursor.execute("select * from `user` where phone = '%s' and password = '%s'" % (username, password))
            # 获取查询结果
            result = cursor.fetchone()
            #print(result)
            connection.commit()
        if (result):
            session = secrets.token_urlsafe(16)
            # 更新登录数据
            cursor.execute("UPDATE user SET session= '%s', sessionTime = '%s' where username = '%s'" % (session, str(int(time.time())), username))
            connection.commit()
            
            userID = result['id']
            # 执行sql语句，进行查询
            sql = "select * from `userData` where userID = '%s' and type = '%s'" % (userID, type)
            cursor.execute(sql)
            result2 = cursor.fetchone()
            connection.commit()
            
            if (result2):
                connection.close()
                dataTemp = ''
                sub = ''
                if (result2['value']):
                    dataTemp = base64.b64decode(result2['value']).decode("utf-8")
                if (result2['sub']):
                    sub = json.loads(result2['sub'])
                if (dataTemp == ''):
                    dataTemp = '{}'
                return json.dumps({"err": 0, "data": {"data": json.loads(dataTemp), "username": result['username'], "session": session, "sourceIp": sourceIp, "userID": userID, "sub": sub}})
            else:
                sql = "INSERT INTO `userData` (userID, type) VALUES ('%s', '%s')" % (userID, type)
                cursor.execute(sql)
                connection.commit()
                connection.close()
                return json.dumps({"err": 0, "data": {"data": '', "username": result['username'], "session": session, "sourceIp": sourceIp, "userID": userID}})
        else:
          return json.dumps({"err": 1, "message": "账号或密码不正确!"})
  else:
    return json.dumps({"err": 1, "message": "账号或密码不能为空!"})


def register(data):
  global config
  body = json.loads(data)
  phone = body['phone']
  code = body['code']
  username = body['username']
  password = body['password']
  if (badSQL(phone) or badSQL(code) or badSQL(username)):
    return {"err": 999, "message": "非法访问!"}
  if username and password and phone:
    # 打开数据库连接
    connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
      cursor.execute("select * from `user` where phone = '%s'" % (phone))
      # 获取查询结果
      userExist = cursor.fetchone()
      if (not userExist):
        return {"err": 1, "message": "请先获取验证码!"}
      if (userExist['verification'] != code):
        return {"err": 1, "message": "验证码错误!"}
      # 执行sql语句，进行查询
      sql = "UPDATE user SET username = '%s', password='%s', state='1' where phone = '%s'" % (username, password, phone)
      print(sql)
      cursor.execute(sql)
      # 获取查询结果
    #   result = cursor.fetchone()
      connection.commit()
      connection.close()
      return json.dumps({"err": 0, "message": "注册成功!"})
  return json.dumps({"err": 1, "message": "缺少必填信息!"})

class loginR(resource.Resource):
  def render_OPTIONS(self, request):
    print('sd')
    return b"ok"
  def render_POST(self, request):
    postData = request.content.read()
    return login(postData).encode('utf-8')

class sendSMSR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return sendSMS(postData).encode('utf-8')

# 获取用户列表

def getUserList(data):
  global config
  body = json.loads(data)
  username = body['username']
  session = body['session']
  if (badSQL(username) or badSQL(session)):
    return {"err": 999, "message": "非法访问!"}
  if username and session:
    # 打开数据库连接
    connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
      cursor.execute("select id, username from `user` where state = '1'")
      connection.commit()
      connection.close()
      # 获取查询结果
      return json.dumps({"err": 0, "data": cursor.fetchall()})
  return json.dumps({"err": 1, "message": "缺少必填信息!"})

class getUserListR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return getUserList(postData).encode('utf-8')


# 获取方案
def getWord():
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("select * from `word`")
    # 获取查询结果
    connection.commit()
    result = cursor.fetchall()
    connection.close()
    return json.dumps({"err": 0, "data": result})

class getWordR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return getWord(postData).encode('utf-8')

# 添加方案
def addWord():
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    sql = "INSERT INTO `word` (type, wordName, wordKey, plan, time) VALUES ('', '新增方案', '', '', '%s')" % (str(int(time.time())))
    print(sql)
    cursor.execute(sql)
    # 获取查询结果
  #   result = cursor.fetchone()
    connection.commit()
    connection.close()
    return getWord()
class addWordR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return addWord(postData).encode('utf-8')

# 保存方案
def saveWord(data):
  body = json.loads(data)
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    sql = "UPDATE word SET wordName = '%s', wordKey='%s', plan='%s' where id = '%s'" % (body['wordName'], body['wordKey'], body['plan'], body['id'])
    print(sql)
    cursor.execute(sql)
    # 获取查询结果
  #   result = cursor.fetchone()
    connection.commit()
    connection.close()
    return getWord()
class saveWordR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return saveWord(postData).encode('utf-8')

# 删除方案
def deleteWord(data):
  body = json.loads(data)
  if (badSQL(body['id'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("DELETE FROM word WHERE id = '%s'" % (body['id']))
    # 获取查询结果
    # result = cursor.fetchone()
    connection.commit()
    connection.close()
    return getWord()
class deleteWordR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return deleteWord(postData).encode('utf-8')

# 添加系统
def addSystem(data):
  body = json.loads(data)
  if (badSQL(body['name']) or badSQL(body['ip']) or badSQL(body['type']) or badSQL(body['remark'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    sql = "INSERT INTO `system` (name, ip, type, remark, isDelete, power) VALUES ('%s', '%s', '%s', '%s', '0', 'admin,')" % (body['name'], body['ip'], body['type'], body['remark'])
    cursor.execute(sql)
    # 获取查询结果
    # result = cursor.fetchone()
    connection.commit()
    connection.close()
    return getSystemP(body['type'])
class addSystemR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return addSystem(postData).encode('utf-8')

# 获取系统
def getSystem(data):
  body = json.loads(data)
  if (badSQL(body['type']) or badSQL(body['username'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    if (body['type'] != 'power'):
      if (body['username'] == 'admin'):
        cursor.execute("select * from `system` WHERE type = '%s' AND isDelete = '0'" % (body['type']))
      else:
        cursor.execute("select * from `system` WHERE type = '%s' AND isDelete = '0' AND power like '%s'" % (body['type'], '%' + body['username'] + ',%'))
    else:
      cursor.execute("select * from `system` WHERE isDelete = '0'")
    # 获取查询结果
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return json.dumps({"err": 0, "data": result})
class getSystemR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return getSystem(postData).encode('utf-8')

# 获取系统信息
def getSystemData(data):
  body = json.loads(data)
  if (badSQL(body['type']) or badSQL(body['name'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("select * from `system` WHERE type = '%s' AND isDelete = '0' AND name = '%s'" % (body['type'], body['name']))
    # 获取查询结果
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return json.dumps({"err": 0, "data": result})
class getSystemDataR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return getSystemData(postData).encode('utf-8')

# 获取系统信息
def getSystemConfig(data):
  body = json.loads(data)
  if (badSQL(body['type']) or badSQL(body['id'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("select config from `system` WHERE type = '%s' AND isDelete = '0' AND id = '%s'" % (body['type'], body['id']))
    # 获取查询结果
    result = cursor.fetchone()
    connection.commit()
    connection.close()
    return json.dumps({"err": 0, "data": result})
class getSystemConfigR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return getSystemConfig(postData).encode('utf-8')

def getSystemP(typeStr):
  if (badSQL(typeStr)):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    if (typeStr != 'power'):
      cursor.execute("select * from `system` WHERE type = '%s' AND isDelete = '0'" % (typeStr))
    else:
      cursor.execute("select * from `system` WHERE isDelete = '0'")
    # 获取查询结果
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return json.dumps({"err": 0, "data": result})


# 删除系统
def deleteSystem(data):
  body = json.loads(data)
  if (badSQL(body['id'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("UPDATE system SET isDelete = '1' where id = '%s'" % (body['id']))
    # 获取查询结果
    connection.commit()
    connection.close()
    return getSystemP(body['type'])
class deleteSystemR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return deleteSystem(postData).encode('utf-8')

# 添加权限
def addPower():
  body = json.loads(data)
  if (badSQL(body['id']) or badSQL(body['data'])):
    return {"err": 999, "message": "非法访问!"}
  # 打开数据库连接
  connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
  with connection.cursor() as cursor:
    # 执行sql语句，进行查询
    cursor.execute("UPDATE system SET power = '%s' where id = '%s'" % (body['data'], body['id']))
    # 获取查询结果
    connection.commit()
    connection.close()
    return getSystemP('power')
class addPowerR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return addPower(postData).encode('utf-8')


# 向其他系统发送数据
def sendMessage():
  body = json.loads(data)
  sendData = urllib.urlencode(body['data'])
  # Is this really the preferred way to pass a string body?
  producer = FileBodyProducer(StringIO(sendData))
  d = self.factory.agent.request('POST', body['url'], Headers({
    'Content-Type': ['application/x-www-form-urlencoded'],
    'User-Agent': ['privacyIDEA-LDAP-Proxy']
  }), producer)
  return d

class sendMessageR(resource.Resource):
  def render_POST(self, request):
    postData = request.content.read()
    return sendMessage(postData).encode('utf-8')


routeList = {
  'login': loginR(),
  'sendSMS': sendSMSR(),
  'getUserList': getUserListR(),
  'getWord': getWordR(),
  'addWord': addWordR(),
  'saveWord': saveWordR(),
  'deleteWord': deleteWordR(),
  'addSystem': addSystemR(),
  'getSystem': getSystemR(),
  'getSystemData': getSystemDataR(),
  'getSystemConfig': getSystemConfigR(),
  'deleteSystem': deleteSystemR(),
  'addPower': addPowerR(),
  'sendMessage': sendMessageR()
}

class enter(resource.Resource):
  def getChild(self, path, request):
    request.setHeader('Content-Type', 'application/json')
    request.setHeader('Access-Control-Allow-Origin', '*')
    request.setHeader('Access-Control-Allow-Headers', 'Origin, Accept, content-type, authorization')
    path = path.decode('utf-8')
    # 路由
    if (path in routeList):
      print('----------------- ' + path + ' -----------------')
      return routeList[path]





site = server.Site(enter())
reactor.listenTCP(8180, site)
reactor.run()