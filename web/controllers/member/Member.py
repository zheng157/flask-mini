# -*- coding: utf-8 -*-
from flask import Blueprint,request,redirect,jsonify
from common.libs.Helper import ops_render,iPagination,getCurrentDate,selectFilterObj,getDictListFilterField,getDictFilterField
from common.models.menber.Menber import Member
from common.models.food.Food import Food
from application import app,db
from common.libs.UrlManager import UrlManager
from common.models.menber.MemberComments import MemberComment



route_member = Blueprint( 'member_page',__name__ )

@route_member.route( "/index" )
def index():
    resp_data = {}
    req = request.values
    page = int(req['p']) if ('p' in req and req['p']) else 1
    query = Member.query
    app.logger.info(page)


    if 'mix_kw' in req:
        query = query.filter(Member.nickname.ilike("%{0}%".format(req['mix_kw'])))


    if 'status' in req and int( req['status'] ) > -1 :
        query = query.filter( Member.status == int( req['status'] ) )

    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }

    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']
    list = query.order_by(Member.id.desc()).offset(offset).limit(app.config['PAGE_SIZE']).all()

    resp_data['list'] = list
    resp_data['pages'] = pages
    resp_data['search_con'] = req
    resp_data['status_mapping'] = app.config['STATUS_MAPPING']

    resp_data['current'] = 'index'

    # app.logger.info(resp_data['status_mapping'])
    # app.logger.info(resp_data)


    return ops_render( "member/index.html" ,resp_data)


@route_member.route( "/info" )
def info():
    resp_data = {}
    req = request.args
    id = int(req.get('id',0))
    reback_url = UrlManager.buildUrl('/member/index')
    if id < 1:
        return redirect(reback_url)

    info = Member.query.filter_by(id = id).first()

    if not info:
        return redirect(reback_url)

    resp_data['info'] = info
    resp_data['current'] = 'index'

    return ops_render( "member/info.html" ,resp_data)

@route_member.route( "/set",methods=['GET','POST'] )
def set():
    if request.method == "GET":
        resp_data = {}
        req = request.args

        id = int(req['id']) if ('id' in req and req['id']) else 0
        reback_url = UrlManager.buildUrl('/member/index')
        if id < 1:
            return redirect(reback_url)

        info = Member.query.filter_by(id=id).first()
        if not info:
            return redirect(reback_url)

        if info.status != 1:
            return redirect(reback_url)

        resp_data['info'] = info
        # app.logger.info(id)
        resp_data['current'] = 'index'

        return ops_render( "member/set.html" ,resp_data)

    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    nickname = req['nickname'] if 'nickname' in req else ''

    if nickname is None or len(nickname) < 2:
        reqs['code'] = -1
        reqs['msg'] = '请输入规范的名字'
        return jsonify(reqs)

    member_info = Member.query.filter_by(id=id).first()
    if not member_info:
        reqs['code'] = -1
        reqs['msg'] = '指定会员不存在'
        return jsonify(reqs)

    member_info.nickname =nickname
    member_info.updated_time = getCurrentDate()

    db.session.add(member_info)
    db.session.commit()
    return jsonify(reqs)


@route_member.route( "/ops",methods=['POST'] )
def ops():
    resp = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    act = req['act'] if 'act' in req else ''

    if not id:
        resp['code'] = -1
        resp['msg'] = "请选择要操作的账号"
        return jsonify(resp)

    if act not in ['remove', 'recover']:
        resp['code'] = -1
        resp['msg'] = "操作有误，请重试"
        return jsonify(resp)

    member_info = Member.query.filter_by(id=id).first()
    if not member_info:
        resp['code'] = -1
        resp['msg'] = "指定会员不存在"
        return jsonify(resp)

    if act == "remove":
        member_info.status = 0
    elif act == "recover":
        member_info.status = 1

    member_info.updated_time = getCurrentDate()
    db.session.add(member_info)
    db.session.commit()
    return jsonify(resp)


@route_member.route( "/comment" )
def comment():
    resp_data = {}
    resp = {'code': 200, 'msg': '操作成功~~', 'data': {}}
    req = request.values
    page = int(req['p']) if ('p' in req and req['p']) else 1

    query = MemberComment.query

    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }

    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']

    comment_list = query.order_by(MemberComment.id.desc()).offset(offset).limit(app.config['PAGE_SIZE']).all()
    # app.logger.info(query)

    data_list = []
    if comment_list:
        member_map = getDictFilterField( Member,Member.id,"id", selectFilterObj( comment_list ,"member_id" ) )
        food_ids = []
        for item in comment_list:
            tmp_food_ids = (item.food_ids[1:-1]).split("_")
            tmp_food_ids = {}.fromkeys(tmp_food_ids).keys()
            food_ids = food_ids + list(tmp_food_ids)

    food_map = getDictFilterField(Food, Food.id, "id", food_ids)



    for item in comment_list:
        tmp_member_info = member_map[item.member_id]
        app.logger.info(tmp_member_info)

        tmp_foods = []
        tmp_food_ids = (item.food_ids[1:-1]).split("_")
        for tmp_food_id in tmp_food_ids:
            tmp_food_info = food_map[int(tmp_food_id)]
            tmp_foods.append({
                'name': tmp_food_info.name,
            })
        # app.logger.info(tmp_foods)
        tmp_data = {
            # 评论内容
            "content": item.content,
            # 打分
            "score": item.score,
            # 姓名
            "member_info": tmp_member_info,
            # 美餐
            "foods": tmp_foods
        }
        data_list.append(tmp_data)

    resp_data['list'] = data_list
    resp_data['pages'] = pages
    resp_data['current'] = 'comment'



    return ops_render( "member/comment.html",resp_data)

