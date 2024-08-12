from application import app
from flask import request,redirect,g
from common.models.user import User
from common.libs.user.UserService import UserService
from common.libs.UrlManager import UrlManager
import re
from common.libs.LogService import LogService




"""
统一拦截器
"""
@app.before_request
def before_request():
    lgnore_urls = app.config['IGNORE_URLS']
    lgnore_check_login_urls = app.config['IGNORE_CHECK_LOGIN_URLS']
    path = request.path
    # 如果是静态文件就不要查询用户信息了
    pattern = re.compile('%s' % '|'.join(lgnore_check_login_urls))
    if pattern.match(path):
        return

    if '/api' in path:
        return


    # 是否登录 check_login()
    user_info = check_login()
    g.current = None
    if user_info:
        g.current_user = user_info


    #加入日志
    LogService.addAccesslog()
    pattern = re.compile('%s' % '|'.join(lgnore_urls))
    if pattern.match(path):
        return


    if not user_info:
        return redirect(UrlManager.buildUrl('/user/login'))

    return


"""
判断用户是否登录
"""
def check_login():
    cookies = request.cookies
    auth_cookie = cookies[app.config['AUTH_COOKIE_NAME']] if app.config['AUTH_COOKIE_NAME'] in cookies else None

    if auth_cookie is None:
        return False


    auth_info = auth_cookie.split("#")
    if len(auth_info) != 2:
        return False

    try:
        user_info = User.query.filter_by(uid = auth_info[1]).first()

    except Exception:
        return False

    if user_info is None:
        return False

    if auth_info[0] != UserService.geneAuthCode(user_info):
        return False

    if user_info.status != 1:
        return False

    return user_info