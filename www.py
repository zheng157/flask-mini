

'''
统一拦截处理和统一错误处理
'''
from web.interceptors.AuthInterceptor import *
from web.interceptors.ApiAuthInterceptor import *
from web.interceptors.ErrorInterceptor import *



'''
蓝图功能，对所有的url进行蓝图功能配置
'''

from application import app
from web.controllers.index import route_index
from web.controllers.user.Uesr import route_user
from web.controllers.account.account import route_account
from web.controllers.static import route_static
from web.controllers.finance.finance import route_finance
from web.controllers.food.food import route_food
from web.controllers.member.Member import route_member
from web.controllers.stat.Stat import route_stat
from web.controllers.api import route_api
from web.controllers.upload.Upload import route_upload
from web.controllers.chart import route_chart



app.register_blueprint(route_index,url_prefix='/')
app.register_blueprint(route_user,url_prefix='/user')
app.register_blueprint(route_static,url_prefix='/static')
app.register_blueprint(route_account,url_prefix='/account')
app.register_blueprint(route_finance,url_prefix='/finance')
app.register_blueprint(route_food,url_prefix='/food')
app.register_blueprint(route_member,url_prefix='/member')
app.register_blueprint(route_stat,url_prefix='/stat')
app.register_blueprint(route_api,url_prefix='/api')
app.register_blueprint(route_upload,url_prefix='/upload')
app.register_blueprint(route_chart,url_prefix='/chart')



