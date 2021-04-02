from flask import Flask, jsonify, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app, supports_credentials=True)

from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor

import re
import json
import time
import base64
import random
import pymysql
import secrets
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入 SMS 模块的client models
from tencentcloud.sms.v20190711 import sms_client, models
# 导入可选配置类
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

appid = 'wxdcfdd904db03fc21'
secret = 'bec3e6576353f72f77cf19b42dd53edc'
def sendMessage(phone, num):
    # 必要步骤：
    # 实例化一个认证对象，入参需要传入腾讯云账户密钥对 secretId 和 secretKey
    # 本示例采用从环境变量读取的方式，需要预先在环境变量中设置这两个值
    # 您也可以直接在代码中写入密钥对，但需谨防泄露，不要将代码复制、上传或者分享给他人
    # CAM 密钥查询：https://console.cloud.tencent.com/cam/capi

    cred = credential.Credential("AKIDKzOWO0EnmUzEBqoRp54okQwwhHadIYhZ", "lHXbCZtw83ScV6RSCfrnY3xaeSzFFcjZ")
    # cred = credential.Credential(
    #     os.environ.get(""),
    #     os.environ.get("")
    # )

    # 实例化一个 http 选项，可选，无特殊需求时可以跳过
    httpProfile = HttpProfile()
    httpProfile.reqMethod = "POST"  # POST 请求（默认为 POST 请求）
    httpProfile.reqTimeout = 30    # 请求超时时间，单位为秒（默认60秒）
    httpProfile.endpoint = "sms.tencentcloudapi.com"  # 指定接入地域域名（默认就近接入）

    # 非必要步骤:
    # 实例化一个客户端配置对象，可以指定超时时间等配置
    clientProfile = ClientProfile()
    clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
    clientProfile.language = "en-US"
    clientProfile.httpProfile = httpProfile

    # 实例化 SMS 的 client 对象
    # 第二个参数是地域信息，可以直接填写字符串 ap-guangzhou，或者引用预设的常量
    client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)

    # 实例化一个请求对象，根据调用的接口和实际情况，可以进一步设置请求参数
    # 您可以直接查询 SDK 源码确定 SendSmsRequest 有哪些属性可以设置
    # 属性可能是基本类型，也可能引用了另一个数据结构
    # 推荐使用 IDE 进行开发，可以方便的跳转查阅各个接口和数据结构的文档说明
    req = models.SendSmsRequest()

    # 基本类型的设置:
    # SDK 采用的是指针风格指定参数，即使对于基本类型也需要用指针来对参数赋值
    # SDK 提供对基本类型的指针引用封装函数
    # 帮助链接：
    # 短信控制台：https://console.cloud.tencent.com/smsv2
    # sms helper：https://cloud.tencent.com/document/product/382/3773

    # 短信应用 ID: 在 [短信控制台] 添加应用后生成的实际 SDKAppID，例如1400006666
    req.SmsSdkAppid = "1400059688"
    # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名，可登录 [短信控制台] 查看签名信息
    req.Sign = "PUGE"
    # 短信码号扩展号: 默认未开通，如需开通请联系 [sms helper]
    req.ExtendCode = ""
    # 用户的 session 内容: 可以携带用户侧 ID 等上下文信息，server 会原样返回
    req.SessionContext = "xxx"
    # 国际/港澳台短信 senderid: 国内短信填空，默认未开通，如需开通请联系 [sms helper]
    req.SenderId = ""
    # 下发手机号码，采用 e.164 标准，+[国家或地区码][手机号]
    # 例如+8613711112222， 其中前面有一个+号 ，86为国家码，13711112222为手机号，最多不要超过200个手机号
    req.PhoneNumberSet = ["+86" + phone]
    # 模板 ID: 必须填写已审核通过的模板 ID，可登录 [短信控制台] 查看模板 ID
    req.TemplateID = "627215"
    # 模板参数: 若无模板参数，则设置为空
    req.TemplateParamSet = [str(num)]


    # 通过 client 对象调用 SendSms 方法发起请求。注意请求方法名与请求对象是对应的
    resp = client.SendSms(req)
    # 输出 JSON 格式的字符串回包
    print(resp.to_json_string(indent=2))


config = {
  "dataBase": {
    "server": "bj-cynosdbmysql-grp-kqvvbnw0.sql.tencentcdb.com",
    "port": 28556,
    "user": "test",
    "password": "test",
    "name": "QHealthier"
  }
}

# 过滤SQL
def badSQL(str):
  return not re.compile('^[0-9A-Za-z\u4e00-\u9fa5\.\-_]+$').findall(str)

@app.route("/")
def index():
  return "Welcome to Flask appliaction created by Serverless Framework."


@app.route("/users")
def users():
  users = [{'name': 'test1'}, {'name': 'test2'}]
  return jsonify(data=users)


@app.route("/users/<id>")
def user(id):
  return jsonify(data={'name': 'test1'})

@app.route("/login", methods=['POST'])
def login():
  global config
  body = json.loads(request.get_data())
  sourceIp = request.remote_addr
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


@app.route("/sendSMS", methods=['POST'])
def sendSMS():
  global config
  body = json.loads(request.get_data())
  phone = body['phone']
  if (badSQL(phone)):
    return {"err": 999, "message": "非法访问!"}
  if phone:
    # 打开数据库连接
    connection = pymysql.connect(host=config["dataBase"]["server"], port=config["dataBase"]["port"], user=config["dataBase"]["user"], password=config["dataBase"]["password"], db=config["dataBase"]["name"], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    with connection.cursor() as cursor:
        cursor.execute("select * from `user` where phone = '%s'" % (phone))
        # 获取查询结果
        userExist = cursor.fetchone()
        code = random.randint(1000, 9999)
        
        sql = "INSERT INTO `user` (username, phone, verification, verificationTime, state) VALUES ('待注册', '%s', '%s', '%s', '0')" % (phone, str(code), str(time.time()))
        if (not userExist):
            cursor.execute(sql)
            #   解码
            connection.commit()
            connection.close()
        sendMessage(phone, str(code))
        return json.dumps({"err": 0, "message": "短信已发送!"})

@app.route("/register", methods=['POST'])
def register():
  global config
  body = json.loads(request.get_data())
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


@app.route("/getUserList", methods=['POST'])
def getUserList():
  global config
  body = json.loads(request.get_data())
  username = body['username']
  session = body['session']
  if (badSQL(username) or badSQL(code) or badSQL(session)):
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



# 岐黄济世

@app.route("/getWord", methods=['GET'])
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


@app.route("/addWord", methods=['GET'])
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


@app.route("/saveWord", methods=['POST'])
def saveWord():
  body = json.loads(request.get_data())
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

@app.route("/deleteWord", methods=['POST'])
def deleteWord():
  body = json.loads(request.get_data())
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


@app.route("/addSystem", methods=['POST'])
def addSystem():
  body = json.loads(request.get_data())
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

@app.route("/getSystem", methods=['POST'])
def getSystem():
  body = json.loads(request.get_data())
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

# 获取系统信息
@app.route("/getSystemData", methods=['POST'])
def getSystemData():
  body = json.loads(request.get_data())
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


@app.route("/deleteSystem", methods=['POST'])
def deleteSystem():
  body = json.loads(request.get_data())
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

@app.route("/addPower", methods=['POST'])
def addPower():
  body = json.loads(request.get_data())
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

if __name__ == '__main__':
  resource = WSGIResource(reactor, reactor.getThreadPool(), app)
  site = Site(resource)
  reactor.listenTCP(8180, site)
  reactor.run()

