from flask import Blueprint,request,jsonify,make_response,redirect,g
import json
from common.models.user import User
from common.libs.user.UserService import UserService
from application import app,db
from common.libs.UrlManager import UrlManager
from common.libs.Helper import ops_render


route_user = Blueprint('user_page',__name__)



@route_user.route('/login',methods=['GET','POST'])
def logon():
    if request.method =="GET":
        return ops_render('user/login.html')
    #req是数组，暂存用户名和密码，用于判断用户名和密码
    req = request.values
    reqs  = {'code':200,'msg':'登录成功','data':{}}
    login_name = req['login_name'] if 'login_name' in req else ''
    login_pwd = req['login_pwd'] if 'login_pwd' in req else ''
    #return "%s --- %s" % (login_name,login_pwd)

    if login_name is None or len(login_name) < 1:
        reqs['code'] = -1
        reqs['msg'] = '你完了，我忘记用户名了，请重新输入！'
        return jsonify(reqs)


    if login_pwd is None or len(login_pwd) < 1:
        reqs['code'] = -1
        reqs['msg'] = '你完了，我忘记密码了，请重新输入！'
        return jsonify(reqs)


    # User.query.filter_by是取数据库表里的XXX数据.first()
    user_info = User.query.filter_by(login_name=login_name,).first()
    if not user_info:
        reqs['code'] = -1
        reqs['msg'] = '请输入正确的登录用户名和密码！-1'
        return jsonify(reqs)



    #判断用户输入的密码和数据库存密码是否致，’user_info.login_pwd‘是数据库存密码，’UserService.genePwd‘是用户输入的密码,
    if user_info.login_pwd != UserService.genePwd(login_pwd,user_info.login_salt):
        reqs['code'] = -1
        reqs['msg'] = '请输入正确的登录用户名和密码！-2'
        return jsonify(reqs)

    if user_info.status != 1:
        reqs['code'] = -1
        reqs['msg'] = '异常，请联系管理员'
        return jsonify(reqs)

    response = make_response(json.dumps({'code': 200, 'msg': '登录成功~~'}))
    response.set_cookie(app.config['AUTH_COOKIE_NAME'], '%s#%s' % (
        UserService.geneAuthCode(user_info), user_info.uid), 60 * 60 * 24 * 120)  # 保存120天
    return response
    # return jsonify(reqs)



@route_user.route('/edit',methods=['GET','POST'])
def edit():
    if request.method == "GET":
        return ops_render( "user/edit.html",{ 'current':'edit' } )

    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}

    req = request.values
    mobile = req['mobile'] if 'mobile' in req else ''
    nickname = req['nickname'] if 'nickname' in req else ''
    email = req['email'] if 'email' in req else ''

    if mobile is None or len(mobile) < 1 :
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的电话'
        return jsonify(reqs)

    if nickname is None or len(nickname) < 1 :
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的姓名'
        return jsonify(reqs)

    if email is None or len(email)< 1 :
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的邮箱'
        return jsonify(reqs)

    #取值写入user_info
    user_info = g.current_user
    user_info.mobile = mobile
    user_info.nickname = nickname
    user_info.email = email

    #更新与写入数据库
    db.session.add(user_info)
    db.session.commit()

    return jsonify(reqs)


@route_user.route('/reset-pwd',methods=['GET','POST'])
def resetPwd():
    if request.method =="GET":
        return ops_render('user/reset_pwd.html',{ 'current':'reset-pwd' })

    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}

    req = request.values
    old_password = req['old_password'] if 'old_password' in req else ''
    new_password = req['new_password'] if 'new_password' in req else ''

    if old_password is None or len(old_password) < 6:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的原密码'
        return jsonify(reqs)

    if new_password is None or len(new_password) < 6 :
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的新密码'
        return jsonify(reqs)

    if old_password == new_password:
        reqs['code'] = -1
        reqs['msg'] = '请重新输入密码，原密码跟新密码相同了'
        return jsonify(reqs)

    user_info = g.current_user
    user_info.login_pwd =UserService.genePwd(new_password,user_info.login_salt)

    db.session.add(user_info)
    db.session.commit()


    #刷新Cookie
    response = make_response(json.dumps(reqs))
    response.set_cookie(app.config['AUTH_COOKIE_NAME'], '%s#%s' % (
        UserService.geneAuthCode(user_info), user_info.uid), 60 * 60 * 24 * 120)  # 保存120天
    return response

    # return jsonify(reqs)



@route_user.route( "/logout" )
def logout():
    response = make_response(redirect(UrlManager.buildUrl("/user/login")))
    response.delete_cookie(app.config['AUTH_COOKIE_NAME'])
    return response
