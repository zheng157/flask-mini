from web.controllers.api import route_api
from flask import request,jsonify,g
from application import app,db
from common.models.food.Food import Food
from common.models.menber.MenberCart import MemberCart
from common.libs.member.CartService import CartService
from common.libs.Helper import selectFilterObj,getDictFilterField
from common.libs.UrlManager import UrlManager
import json

@route_api.route('/cart/index')
def cart_index():
    reqs = {'code': 200, 'msg': '添加购物车成功', 'data': {}}

    member_info = g.member_info
    if not member_info:
        reqs['code'] = -1
        reqs['msg'] = '获取失败，未登录'
        return jsonify(reqs)

    cart_list = MemberCart.query.filter_by( member_id=member_info.id).all()

    # app.logger.info(cart_list)
    data_cart_lit = []
    if cart_list:
        # food_ids是member_cart表
        food_ids = selectFilterObj( cart_list,"food_id" )
        # food_map 是food表
        food_map = getDictFilterField(Food,Food.id,'id',food_ids)

        for item in cart_list:
            tmp_food_info = food_map[item.food_id]
            tmp_data = {
                "id": item.id,
				"food_id":item.food_id,
                "number": item.quantity,
                "pic_url":UrlManager.buildImageUrl(tmp_food_info.main_image),
                "name": tmp_food_info.name,
                "price": str(tmp_food_info.price) ,
                "active": True
                }

            data_cart_lit.append(tmp_data)
    reqs['data']['list'] = data_cart_lit
    return jsonify(reqs)

# 添加购物车里的商品
@route_api.route('/cart/set',methods=['POST'])
def cart_set():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    food_id = int(req['id']) if 'id' in req else 0
    number = int(req['number']) if 'number' in req else ''

    if food_id <1 or number < 1:
        reqs['code'] = -1
        reqs['msg'] = '添加失败 -1'
        return jsonify(reqs)

    member_info = g.member_info
    if not member_info:
        reqs['code'] = -1
        reqs['msg'] = '添加失败 -2'
        return jsonify(reqs)

    food_info = Food.query.filter_by(id=food_id).first()

    if not food_info:
        reqs['code'] = -1
        reqs['msg'] = '添加失败 -3'
        return jsonify(reqs)


    if food_info.stock < number:
        reqs['code'] = -1
        reqs['msg'] = '添加失败,库存不足'
        return jsonify(reqs)

    # app.logger.info(member_info.id)
    # app.logger.info(food_id)
    # app.logger.info(number)
    ret = CartService.setItems(member_id=member_info.id,food_id =food_id,number =number)
    if not ret:
        reqs['code'] = -1
        reqs['msg'] = '添加失败 -4'
        return jsonify(reqs)

    return jsonify(reqs)

# 删除购物车里的商品
@route_api.route('/cart/del',methods=['POST'])
def cart_del():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    params_goods = req['goods'] if 'goods' in req else None

    app.logger.info(params_goods)

    items = []
    if params_goods:
        items = json.loads(params_goods)

    app.logger.info(items)
    if not items or len(items ) < 1:
        return jsonify(reqs)

    member_info = g.member_info
    app.logger.info(member_info)
    if not member_info:
        reqs['code'] = -1
        reqs['msg'] = '删除购物车失败 -1'
        return jsonify(reqs)

    ret = CartService.deleteItem(member_id= member_info.id,items = items)
    app.logger.info(ret)
    if not ret:
        reqs['code'] = -1
        reqs['msg'] = '删除购物车失败 -2'
        return jsonify(reqs)

    return jsonify(reqs)
