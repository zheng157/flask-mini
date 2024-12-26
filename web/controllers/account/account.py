from flask import Blueprint,request,redirect,jsonify
from common.libs.Helper import ops_render,iPagination,getCurrentDate
from common.models.user import User
from common.libs.UrlManager import UrlManager
from common.libs.user.UserService import UserService
from sqlalchemy import or_
from application import app,db
from common.models.loh.AppAccesslog import AppAccessLog



route_account = Blueprint('account',__name__)


@route_account.route('/index',methods = [ 'GET','POST'])
def index():
    resp_data = {}
    req = request.values
    page = int(req['p'] if ('p' in req and req['p']) else 1)
    query = User.query
    # app.logger.info(req)
    # app.logger.info(page)


    if 'mix_kw' in req:
        #查询用户名和电话，用的是混合查询
        rule = or_(User.nickname.ilike("%{0}%".format(req['mix_kw'])), User.mobile.ilike("%{0}%".format(req['mix_kw'])))
        query = query.filter(rule)

        # 用的是对等查询 0是已删除  1是正常
    if 'status' in req and int(req['status']) > -1:
        query = query.filter(User.status == int(req['status']))


    # query.count()是总页数
    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }

    # app.logger.info(page_params)
    #分页是在这里写的
    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']
    limit = app.config['PAGE_SIZE'] * page

    list = query.order_by( User.uid.desc() ).all()[ offset:limit ]

    resp_data['list'] = list
    resp_data['pages'] = pages
    resp_data['search_con'] = req
    resp_data['status_mapping'] = app.config['STATUS_MAPPING']


    return ops_render('account/index.html',resp_data)


@route_account.route( "/info" )
def info():
    resp_data = {}
    req = request.args
    uid = int( req.get('id',0))
    reback_url =  UrlManager.buildUrl( "/account/index" )
    if uid < 1:
        return redirect( reback_url )

    info = User.query.filter_by( uid = uid).first()
    if not info:
        return redirect( reback_url )

    #写入访问记录
    # access_list = AppAccessLog.query.filter_by( uid = uid).order_by(AppAccessLog.id.desc() ).limit(10).all()
    # resp_data['info'] = info
    # resp_data['access_list'] = access_list
    # app.logger.info(app.config['PAGE2_DISPLAY'])

    """
     分页
    # """
    req = request.values
    page = int(req['p']) if ('p' in req and req['p']) else 1
    query = AppAccessLog.query

    # PAGE_SIZE = 50
    # PAGE_DISPLAY = 10

    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE2_SIZE'],
        'page': page,
        'display': app.config['PAGE2_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }

    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE2_SIZE']
    limit = app.config['PAGE2_SIZE'] * page

    # 写入访问记录
    # access_list = AppAccessLog.query.filter_by(uid=uid).order_by(AppAccessLog.id.desc()).limit(10).all()
    # access_list = query.order_by(AppAccessLog.uid.desc()).all()[offset:limit]

    access_list = AppAccessLog.query.filter_by(uid=uid).order_by(AppAccessLog.id.desc()).all()[offset:limit]

    resp_data['access_list'] = access_list
    resp_data['pages'] = pages
    resp_data['search_con'] = req
    resp_data['status_mapping'] = app.config['STATUS_MAPPING']
    resp_data['info'] = info


    app.logger.info(app.config['PAGE2_SIZE'])
    app.logger.info(app.config['PAGE2_DISPLAY'])



    return ops_render('account/info.html',resp_data)

@route_account.route('/set',methods=['GET','POST'])
def set():
    default_pwd = "******"

    if request.method == "GET":
        resp_data = {}
        req = request.args
        uid = int(req.get("id",0))
        # reback_url = UrlManager.buildUrl('/account/index')
        # user_info = User.query.filter_by(uid=id).first()
        #
        # if id != user_info.uid:
        #     return redirect(reback_url)
        #
        # if user_info.status != 1:
        #     return redirect(reback_url)

        user_info = None
        if uid:
            user_info = User.query.filter_by(uid= uid).first()

        resp_data['user_info'] = user_info
        return ops_render('account/set.html',resp_data)

    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    nickname = req['nickname'] if 'nickname' in req else ''
    mobile = req['mobile'] if 'mobile' in req else ''
    email = req['email'] if 'email' in req else ''
    login_name = req['login_name'] if 'login_name' in req else ''
    login_pwd = req['login_pwd'] if 'login_pwd' in req else ''


    if nickname is None or len(nickname) < 2:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的名字'
        return jsonify(reqs)

    if mobile is None or len(mobile) < 2:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的电话'
        return jsonify(reqs)

    if email is None or len(email) < 2:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的邮箱'
        return jsonify(reqs)

    if login_name is None or len(login_name) < 2:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的登录名'
        return jsonify(reqs)

    if login_pwd is None or len(login_pwd) < 6:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的登录密码'
        return jsonify(reqs)

    #判断用户名是否重复
    has_in = User.query.filter( User.login_name == login_name,User.uid != id ).first()

    if has_in:
        reqs['code'] = -1
        reqs['msg'] = '该登录名已存在，请换一个试试'
        return jsonify(reqs)

    user_info = User.query.filter_by( uid = id ).first()

    if user_info:
        model_user = user_info #编辑
    else:
        #新增
        model_user = User()
        model_user.created_time = getCurrentDate()
        model_user.login_salt = UserService.geneSalt()

    model_user.nickname = nickname
    model_user.mobile = mobile
    model_user.email = email
    model_user.login_name = login_name
    if login_pwd != default_pwd:
        model_user.login_pwd = UserService.genePwd( login_pwd,model_user.login_salt)
    model_user.updated_time = getCurrentDate()


    db.session.add(model_user)
    db.session.commit()

    return jsonify(reqs)


@route_account.route('/ops',methods=['POST'])
def ops():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    act = req['act'] if 'act' in req else ''

    # app.logger.info(req)

    if not id:
        reqs['code'] = -1
        reqs['msg'] = '请选择要操作的账号'
        return jsonify(reqs)

    if  act not in [ 'remove','recover' ] :
        reqs['code'] = -1
        reqs['msg'] = "操作有误，请重试~~"
        return jsonify(reqs)

      #查询id是否存在
    user_info = User.query.filter_by(uid=id).first()
    if not user_info:
        reqs['code'] = -1
        reqs['msg'] = '账号不存在'
        return jsonify(reqs)

    if act == "remove":
        user_info.status = 0
    elif act == "recover":
        user_info.status = 1

    user_info.update_time = getCurrentDate()
    db.session.add(user_info)
    db.session.commit()
    return jsonify(reqs)

