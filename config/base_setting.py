#外配置文件
import os
SERVER_POET = 1999
DEBUG = False
SQLALCHEMY_ECHO = False
SQLALCHEMY_DATABASE_URI = 'mysql://imooc:666666@47.121.116.233/food_db?charset=utf8'
SQLALCHEMY_TRACK_MODIFICATIONS = False



AUTH_COOKIE_NAME = 'mooc_food'


#过滤url
IGNORE_URLS = [
    "^/user/login",
]
API_IGNORE_URLS = [
    "^/api"
]

IGNORE_CHECK_LOGIN_URLS = [
    "^/static",
    "^/favicon.ico"
]

# 设置多少条页
PAGE_SIZE = 10

PAGE2_SIZE = 10
# 设置多少数据
PAGE_DISPLAY = 10

PAGE2_DISPLAY = 10

STATUS_MAPPING = {
    '1':'正常',
    '0':'已删除'
}
# 设置js
# RELEASE_VERSION = {20231113}

MIN_APP = {
    'appid':'wxb3afa165313888dd',
    'appkey':'b0629706c2af62240b6ce4438137a387',
    # 商户的key
    'paykey':'',
    # 商户的id号
    'mch_id':'',
    'callback_url':'/api/order/callback'
}

# MIN_APPID = 'wxb3afa165313888dd'
# MIN_APPKEY = 'wxb3afa165313888dd'

UPLOAD = {
    'ext':[ 'jpg','gif','bmp','jpeg','png' ],
    'prefix_path':'/web/static/upload/',
    'prefix_url':'/static/upload/'
}

API= {
    'domain' : 'http://47.121.116.233:1999'

}
PAY_STATUS_MAPPING = {
    "1":"已支付",
    "-8":"待支付",
    "0":"已关闭",

}



PAY_STATUS_DISPLAY_MAPPING = {
        "0":"订单关闭",
        "1":"支付成功",
        "-8":"待支付",
        "-7":"待发货",
        "-6":"待确认",
        "-5":"待评价"
}



