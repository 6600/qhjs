from twisted.web import server, resource
from twisted.internet import reactor
import re
import json
import time
import base64
import random
import pymysql
import secrets

# 读取配置文件
config = json.loads(open('./config.json', 'r').read())
print(config)

# 过滤SQL
def badSQL(str):
  return not re.compile('^[0-9A-Za-z\u4e00-\u9fa5\.\-_]+$').findall(str)


class errorR(resource.Resource):
  def render_OPTIONS(self, request):
    return b"ok"
  def render_GET(self, request):
    return json.dumps({"err": 1}).encode('utf-8')


def getConfig():
  global config
  print(config)
  return json.dumps({"err": 0, "data": config})

class getConfigR(resource.Resource):
  def render_OPTIONS(self, request):
    return b"ok"
  def render_GET(self, request):
    return getConfig().encode('utf-8')


routeList = {
  'error': errorR,
  'getConfig': getConfigR,
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
      return routeList[path]()
    else:
      return routeList['error']()




print('server running at 8181 port!')
site = server.Site(enter())
reactor.listenTCP(8181, site)
reactor.run()