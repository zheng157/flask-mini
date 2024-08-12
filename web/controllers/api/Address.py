from web.controllers.api import route_api
from flask import request,jsonify,g
from common.models.menber.MemberAddress import MemberAddres
from application import app,db
from common.models.pay.PayOrder import PayOrder
from common.models.pay.PayOrderItem import PayOrderItem
from common.models.menber.MemberComments import MemberComment
from common.models.food.Food import Food
from common.libs.Helper import selectFilterObj,getDictFilterField,getCurrentDate
from common.libs.UrlManager import UrlManager
from common.libs.pay.WeChatService import WeChatService
import json

# 发货地址
@route_api.route('/my/address/index')
def my_address_index():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    member_info = g.member_info

    address_info =  MemberAddres.query.filter_by(member_id=member_info.id,status = 1)\
        .order_by(MemberAddres.id.desc()).all()

    data_inst = []
    if address_info:
        for item in address_info:
            tmp_data = {
                "id": item.id,
                "nickname":item.nickname,
                "mobile":item.mobile,
                "address": "%s%s%s%s" % (item.province_str,item.city_str,item.area_str,item.address),
                "is_default":item.is_default,
            }
            data_inst.append(tmp_data)
    reqs['data']['list'] = data_inst
    return jsonify(reqs)

@route_api.route('/my/address/ops',methods=[ "POST"])
def my_address_ops():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    id = int(req['id']) if 'id' in req else 0
    act = req['act'] if 'act' in req else ''
    member_info = g.member_info

    addresd_info = MemberAddres.query.filter_by(id = id ,member_id = member_info.id).first()

    if not addresd_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)

    app.logger.info(act)
    # 删除判断
    if act == "del":
        app.logger.info("*"*50)
        addresd_info.status = 0
        addresd_info.updated_time = getCurrentDate()
        db.session.add(addresd_info)
        db.session.commit()

    elif act == "default":
        # MemberAddres里的is_default为0
        MemberAddres.query.filter_by(member_id = member_info.id).update({"is_default":0})
        addresd_info.is_default = 1
        addresd_info.updated_time = getCurrentDate()
        db.session.add(addresd_info)
        db.session.commit()


    return jsonify(reqs)

@route_api.route('/my/address/set',methods=[ "POST"])
def my_address_set():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    # id = int(req['id']) if 'id' in req else 0
    if 'id' in req:
        id_str = req['id']
        if id_str.isdigit():  # 检查字符串是否只包含数字
            id = int(id_str)
        else:
            id = 0  # 或者你可以选择引发一个异常
    else:
        id = 0
    # 省id代码
    province_id = int(req['province_id']) if ('province_id' in req and req['province_id']) else 0
    # 市id代码
    city_id = int( req['city_id'] ) if (  'city_id' in req  and  req['city_id'])else 0
    # 镇id代码
    area_id = int( req['area_id'] ) if ( 'area_id' in req and req['area_id'] ) else 0
    # 省
    province_str = req['province_str'] if 'province_str' in req else ''
    # 市
    city_str = req['city_str'] if 'city_str' in req else ''
    # 镇
    area_str = req['area_str'] if 'area_str' in req else ''

    # 名字
    nickname = req['nickname'] if 'nickname' in req else ''
    # 详细地址
    address = req['address'] if 'address' in req else ''
    # 电话
    mobile = int(req['mobile']) if 'mobile' in req else 0

    member_info = g.member_info

    if not nickname:
        reqs['code'] = -1
        reqs['msg'] = '请填写联系人姓名'
        return jsonify(reqs)

    if not mobile or  mobile <2:
        reqs['code'] = -1
        reqs['msg'] = '请填写手机号码'
        return jsonify(reqs)

    if province_id < 1:
        reqs['code'] = -1
        reqs['msg'] = '请选择地区'
        return jsonify(reqs)

    if city_id < 1:
        reqs['code'] = -1
        reqs['msg'] = '请选择地区'
        return jsonify(reqs)

    if area_id <1:
        area_str = ''

    if not address:
        reqs['code'] = -1
        reqs['msg'] = '请填写详细地址'
        return jsonify(reqs)
    address_info = MemberAddres.query.filter_by(id = id ,member_id= member_info.id).first()
    # 判断如果有就继续保存
    if address_info:
        model_address = address_info
    # 判断没如果有就创新保存
    else:
        default_address_count =MemberAddres.query.filter_by( is_default = 1,member_id = member_info.id ,status = 1).count()
        model_address = MemberAddres()
        model_address.member_id = member_info.id
        model_address.is_default = 1 if default_address_count == 0 else 0
        model_address.created_time = getCurrentDate()

    model_address.province_id = province_id
    model_address.city_id = city_id
    model_address.area_id = area_id

    model_address.province_str = province_str
    model_address.city_str = city_str
    model_address.area_str = area_str

    model_address.nickname = nickname
    model_address.address = address
    model_address.mobile = mobile
    model_address.updated_time = getCurrentDate()
    db.session.add(model_address)
    db.session.commit()

    return jsonify(reqs)

# 补地址信息
@route_api.route('/my/address/info')
def my_address_info():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    id = int(req['id']) if 'id' in req else 0
    member_info = g.member_info
    if id <1 or not member_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙，请稍后再试'
        return jsonify(reqs)

    address_info = MemberAddres.query.filter_by(id = id ,member_id =member_info.id ).first()
    if not address_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙，请稍后再试'
        return jsonify(reqs)

    reqs['data']['info'] = {
        "nickname": address_info.nickname,
        "mobile": address_info.mobile,
        "address": address_info.address,
        "province_id": address_info.province_id,
        "province_str": address_info.province_str,
        "city_id": address_info.city_id,
        "city_str": address_info.city_str,
        "area_id": address_info.area_id,
        "area_str": address_info.area_str
    }

    return jsonify(reqs)
