from common.models.pay.PayOrder import PayOrder
from web.controllers.api import route_api
from flask import request,jsonify,g
from application import app,db
from common.models.food.Food import Food
from common.models.menber.MemberAddress import MemberAddres
from common.libs.member.CartService import CartService
from common.libs.Helper import selectFilterObj,getDictFilterField,getCurrentDate
from common.libs.UrlManager import UrlManager
from common.models.menber.Oauth_member_bind import OauthMemberBind
from common.libs.pay.WeChatService import WeChatService
from common.libs.pay.PayService import PayServce
import json,decimal




@route_api.route('/order/info',methods=['POST'])
def order_index():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    params_goods = req['goods'] if 'goods' in req else None
    member_info = g.member_info
    params_goods_list =[]
    if params_goods:
        params_goods_list = json.loads(params_goods)

    food_dic = {}
    for item in params_goods_list:
        food_dic[item['id']] = item['number']

    food_ids = food_dic.keys()
    food_list = Food.query.filter(Food.id.in_(food_ids)).all()
    data_food_list = []
    yun_price = pay_price = decimal.Decimal(0.00)
    if food_list:
        for item in food_list:
            tmp_data = {
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'pic_url': UrlManager.buildImageUrl(item.main_image),
                'number': food_dic[item.id],
            }
            pay_price = pay_price + item.price * int(food_dic[item.id])
            data_food_list.append(tmp_data)

    address_info = MemberAddres.query.filter_by( is_default = 1,member_id = member_info.id,status = 1 ).first()
    default_address = ''
    if address_info:
        default_address ={
            "id":address_info.id,
            "nickname:":address_info.nickname,
            "zheng": address_info.nickname,
            "mobile": address_info.mobile,
            "address":"%s%s%s%s"%(address_info.province_str,address_info.city_str,address_info.area_str,address_info.address,)
        }
    # app.logger.info(address_info)
    # app.logger.info(default_address)
    # 商品
    reqs['data']['food_list'] = data_food_list
    # 商品金额
    reqs['data']['pay_price'] = str(pay_price)
    # 运费
    reqs['data']['yun_price'] = str(yun_price)
    # 合计
    reqs['data']['total_price'] = str(pay_price+yun_price)
    # 地址
    reqs['data']['default_address'] = default_address

    return jsonify(reqs)



@route_api.route('/order/create',methods=['POST'])
def order_create():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    params_goods = req['goods'] if 'goods' in req else None
    express_address_id = int(req['express_address_id']) if 'express_address_id' in req and req['express_address_id'] else 0
    type = req['type'] if 'type' in req else ''
    # app.logger.info(express_address_id)
    items = []
    if params_goods:
        items = json.loads(params_goods)

    if len(items) < 1:
        reqs['code'] = -1
        reqs['msg'] = '下单失败，没有选择商品'
        return jsonify(reqs)

    address_info = MemberAddres.query.filter_by(id = express_address_id).first()
    if not address_info or not address_info.status:
        reqs['code'] = -1
        reqs['msg'] = '下单失败，快递地址不对'
        return jsonify(reqs)


    member_info = g.member_info
    params = {
        "express_address_id":address_info.id,
        "express_info":{
            "nickname": address_info.nickname,
            "mobile": address_info.mobile,
            "address": "%s%s%s%s" % (address_info.province_str, address_info.city_str, address_info.area_str, address_info.address)
        }
    }
    # app.logger.info(params)
    # app.logger.info("*" * 50)
    # params = json.dumps(params,ensure_ascii=False)
    # app.logger.info("*" * 50)
    # app.logger.info(params)

    target = PayServce()
    reqs = target.createOrder(member_info.id,items,params)
    if reqs['code'] ==200 and type == 'cart':
        CartService.deleteItem(member_info.id,items)
    return jsonify(reqs)

# 下单
@route_api.route('/order/pay', methods=[ "POST"])
def order_pay():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    member_info = g.member_info
    req = request.values
    order_sn = req['order_sn'] if 'order_sn' in req else ''

    # 表 pay_order
    pay_order_info = PayOrder.query.filter_by( order_sn = order_sn).first()
    if not pay_order_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)
    # 表 oauth_member_bind
    oauth_bind_info = OauthMemberBind.query.filter_by(member_id = member_info.id).first()
    if not oauth_bind_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)

    config_mina = app.config['MIN_APP']
    notify_url = app.config['API']['domain'] + config_mina['callback_url']
    target_wechat = WeChatService()
    # target_wechat = WeChatService(merchant_key=config_mina['paykey'])
    data = {
        'appid': config_mina['appid'],
        'mch_id': config_mina['mch_id'],
        'nonce_str': target_wechat.get_nonce_str(),
        'body': '订餐',  # 商品描述
        'out_trade_no': pay_order_info.order_sn,  # 商户订单号
        'total_fee': int(pay_order_info.total_price * 100),
        'notify_url': notify_url,
        'trade_type': "JSAPI",
        'openid': oauth_bind_info.openid
    }
    # pay_info = target_wechat.get_pay_info(data)
    # 保存prepay_id为了后面发模板消息
    # pay_order_info.prepay_id = "无第三方预付id"
    pay_order_info.prepay_id = req['can_send'] if 'can_send' in req else 0
    # pay_order_info.prepay_id = pay_info['prepay_id']
    db.session.add(pay_order_info)
    db.session.commit()

    app.logger.info("#" * 50)
    target_pay = PayServce()
    target_pay.orderSuccess(pay_order_id=pay_order_info.id, params={"pay_sn": "无第三方流水号"})

    # 将微信回调的结果写入记录表
    target_pay.addPayCallbackData(pay_order_id=pay_order_info.id, data=data)
    app.logger.info("#" * 50)

    reqs['data']['pay_info'] = data
    return jsonify(reqs)

@route_api.route('/order/ops', methods=[ "POST"])
def order_ops():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    member_info = g.member_info
    req = request.values

    order_sn = req['order_sn'] if 'order_sn' in req else ''
    act = req['act'] if 'act' in req else ''

    pay_order_info = PayOrder.query.filter_by(order_sn = order_sn, member_id = member_info.id).first()

    if not pay_order_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)

    if act == "cancel":
        target_pay = PayServce()
        ret = target_pay.closeOrder(pay_order_id = pay_order_info.id)
        if not ret:
            reqs['code'] = -1
            reqs['msg'] = '系统繁忙。请稍后再试'
            return jsonify(reqs)

    elif act == "confirm":

        pay_order_info.express_status = 1
        pay_order_info.updated_time = getCurrentDate()
        db.session.add(pay_order_info)
        db.session.commit()


    return jsonify(reqs)

# web模拟回调方法
# 其实所有回调基本都是校验合法性 然后找到订单id，所以我们模拟就是直接传递 订单id
# 详解可以看博文：http://www.jixuejima.cn/article/281.html
# 访问Url就是  http://xxxxxx(你的ip或者域名)/api/order/callback2?id=yyyy
# 其中yyyy 就是你订单表的id字段的值
# 解析微信回调2
# @route_api.route("/order/callback2")
# def orderCallback2():
#     req = request.values
#     id =  int(req['id']) if 'id' in req else 0
#     if not id:
#         return "fail"
#     target_pay = PayServce()
#     target_pay.orderSuccess(pay_order_id=id, params={"pay_sn": ""})
#     return "success",id


# 解析微信回调
# @route_api.route("/order/callback", methods=["POST"])
# def orderCallback():
#     result_data = {
#         'return_code': 'SUCCESS',
#         'return_msg': 'OK'
#     }
#     header = {'Content-Type': 'application/xml'}
#     config_mina = app.config['MIN_APP']
#     target_wechat = WeChatService(merchant_key=config_mina['paykey'])
#     callback_data = target_wechat.xml_to_dict(request.data)
#     app.logger.info(callback_data)
#
#     sign = callback_data['sign']
#     callback_data.pop('sign')
#     gene_sign = target_wechat.create_sign(callback_data)
#     app.logger.info(gene_sign)
#
#     if sign != gene_sign:
#         result_data['return_code'] = result_data['return_msg'] = 'FAIL'
#         return target_wechat.dict_to_xml(result_data), header
#
#     if callback_data['result_code'] != 'SUCCESS':
#         result_data['return_code'] = result_data['return_msg'] = 'FAIL'
#         return target_wechat.dict_to_xml(result_data), header
#
#     order_sn = callback_data['out_trade_no']
#     # order_sn = PayOrder.order_sn
#
#     pay_order_info = PayOrder.query.filter_by(order_sn=order_sn).first()
#
#     if not pay_order_info:
#         result_data['return_code'] = result_data['return_msg'] = 'FAIL'
#         return target_wechat.dict_to_xml(result_data), header
#
#     if int(pay_order_info.total_price * 100) != int(callback_data['total_fee']):
#         result_data['return_code'] = result_data['return_msg'] = 'FAIL'
#         return target_wechat.dict_to_xml(result_data), header
#
#     if pay_order_info.status == 1:
#         return target_wechat.dict_to_xml(result_data), header
#
#     target_pay = PayServce()
#     target_pay.orderSuccess(pay_order_id=pay_order_info.id, params={"pay_sn": callback_data['transaction_id']})
#     # 将微信回调的结果写入记录表
#     target_pay.addPayCallbackData(pay_order_id=pay_order_info.id, data=request.data)
#
#     return target_wechat.dict_to_xml(result_data), header








