from web.controllers.api import route_api
from flask import request,jsonify,g
from application import app,db
from common.models.menber.Menber import Member
from common.models.menber.Oauth_member_bind import OauthMemberBind
import requests,json
from common.libs.Helper import getCurrentDate
from common.libs.member.MemberService import MemberService
from common.models.food.WxShareHistory import WxShareHistory


@route_api.route('/member/login',methods=['GET','POST'])
#注册用户
def member_login():
    reqs = {'code': 200, 'msg': '登录成功', 'data': {}}

    #获取到用户信息
    req = request.values
    code = req['code'] if 'code' in req else ''
    if not code or len(code) < 1:
        reqs['code'] = -1
        reqs['msg'] = '需要code'
        return jsonify(reqs)

    app.logger.info(code)


    # 生成openid，生成openid需要code，code从req里拿
    openid = MemberService.getWeChatOpenid(code)
    if openid is None:
        reqs['code'] = -1
        reqs['msg'] = '需要openid'
        return jsonify(reqs)

    app.logger.info(openid)

    nickname = req['nickName'] if 'nickName' in req else ''
    sex = req['gender'] if 'gender' in req else 0
    avatar = req['avatarUrl'] if 'avatarUrl' in req else ''

    """
    判断是否已经测试过，注册了直接返回一些信息
    """
    bind_info = OauthMemberBind.query.filter_by(openid=openid, type=1).first()
    if not bind_info:
        # 把数据写进Member表
        model_member = Member()
        model_member.nickname = nickname
        model_member.sex = sex
        model_member.avatar = avatar
        # salt用方法自动生成
        model_member.salt = MemberService.geneSalt()
        model_member.updated_time = model_member.created_time = getCurrentDate()
        db.session.add(model_member)
        db.session.commit()

        # 把数据写进OauthMemberBind表
        model_bind = OauthMemberBind()
        model_bind.member_id = model_member.id
        model_bind.type = 1
        model_bind.openid = openid
        model_bind.extra = ''
        model_bind.updated_time = model_bind.created_time = getCurrentDate()
        db.session.add(model_bind)
        db.session.commit()

        bind_info = model_bind

    # app.logger.info(bind_info)
    member_info = Member.query.filter_by(id=bind_info.member_id).first()

    # token是Cookie
    token = "%s#%s" % (MemberService.geneAuthCode(member_info),member_info.id)

    reqs['data'] = {"token": token}
    return jsonify(reqs)


@route_api.route('/member/check-reg',methods=['GET','POST'])
#判断是否是注册过的用户
def member_checkreg():
    reqs = {'code': 200, 'msg': '登录成功', 'data': {}}
    req = request.values

    code = req['code'] if 'code' in req else ''
    if not code or len(code) < 1:
        reqs['code'] = -1
        reqs['msg'] = '需要code'
        return jsonify(reqs)


    openid = MemberService.getWeChatOpenid(code)
    if openid is None:
        reqs['code'] = -1
        reqs['msg'] = '需要openid'
        return jsonify(reqs)

    bind_info = OauthMemberBind.query.filter_by(openid=openid, type=1).first()
    if not bind_info:
        reqs['code'] = -1
        reqs['msg'] = '未绑定'
        return jsonify(reqs)

    member_info = Member.query.filter_by(id=bind_info.member_id).first()
    if not member_info:
        reqs['code'] = -1
        reqs['msg'] = '未查询到绑定信息'
        return jsonify(reqs)

    #token是Cookie
    token = "%s#%s" % (MemberService.geneAuthCode(member_info),member_info.id)

    reqs['data'] = {"token" : token}
    return jsonify(reqs)

# 微信分享记录
@route_api.route('/member/share',methods=['GET','POST'])
def member_share():
    reqs = {'code': 200, 'msg': '操作成功~', 'data': {}}
    req = request.values
    url = req['url'] if 'url' in req else ''
    member_info = g.member_info
    model_share = WxShareHistory()
    if member_info:
        model_share.member_id = member_info.id
    # app.logger.info(g)
    model_share.share_url = url
    model_share.created_time = getCurrentDate()

    db.session.add(model_share)
    db.session.commit()
    return jsonify(reqs)

# 显示主页用户信息
@route_api.route('/member/info')
def member_info():
    reqs = {'code': 200, 'msg': '操作成功~', 'data': {}}

    member_info = g.member_info
    app.logger.info(member_info)
    member = Member.query.filter_by(id = member_info.id,status = 1).first()
    if not member:
        reqs['code'] = -1
        reqs['msg'] = '出问题'
        return jsonify(reqs)

    user_info = {
        'nickname':member.nickname,
        'avatar_url':member.avatar,
    }
    reqs['data']['user_info'] = user_info

    return jsonify(reqs)

