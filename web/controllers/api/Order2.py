from common.models.pay.PayOrder import PayOrder
from web.controllers.api import route_api
from flask import request,jsonify,g
from application import app,db
from common.models.food.Food import Food
from common.libs.member.CartService import CartService
from common.libs.Helper import selectFilterObj,getDictFilterField
from common.libs.UrlManager import UrlManager
from common.libs.pay.PayService2 import PayServce2
from common.models.menber.Oauth_member_bind import OauthMemberBind
from common.libs.pay.WeChatService2 import WeChatService2
import json,decimal




@route_api.route('/order/info2',methods=['POST'])
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

    default_address ={
        'name:': "编程浪子",
        'mobile': "12345678901",
        'detail':"上海市浦东新区XX",
    }
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


@route_api.route('/order/create2',methods=['POST'])
def order_create():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    params_goods = req['goods'] if 'goods' in req else None
    type = req['type'] if 'type' in req else ''

    items = []
    if params_goods:
        items = json.loads(params_goods)

    if len(items) < 1:
        reqs['code'] = -1
        reqs['msg'] = '下单失败，没有选择商品'
        return jsonify(reqs)
    member_info = g.member_info
    params = {}

    target = PayServce2()
    reqs = target.createOrder2(member_info.id,items,params)
    if reqs['code'] ==200 and type == 'cart':
        CartService.deleteItem(member_info.id,items)
    return jsonify(reqs)

# 下单
@route_api.route('/order/pay2', methods=[ "POST"])
def order_pay():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    member_info = g.member_info
    req = request.values
    order_sn = req['order_sn'] if 'order_sn' in req else ''
    pay_order_info = PayOrder.query.filter_by( order_sn = order_sn).first()
    if not pay_order_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)

    oauth_bind_info = OauthMemberBind.query.filter_by(member_id = member_info.id).first()
    if not oauth_bind_info:
        reqs['code'] = -1
        reqs['msg'] = '系统繁忙。请稍后再试'
        return jsonify(reqs)

    config_mina = app.config['MIN_APP']
    notify_url = app.config['API']['domain'] + config_mina['callback_url']

    target_wechat = WeChatService2(merchant_key=config_mina['paykey'])

    data = {
        'appid': config_mina['appid'],
        'mch_id': config_mina['mch_id'],
        'nonce_str': target_wechat.get_nonce_str2(),
        'body': '订餐',  # 商品描述
        'out_trade_no': pay_order_info.order_sn,  # 商户订单号
        'total_fee': int(pay_order_info.total_price * 100),
        'notify_url': notify_url,
        'trade_type': "JSAPI",
        'openid': oauth_bind_info.openid
    }
    pay_info = target_wechat.get_pay_info2(data)

    # 保存prepay_id为了后面发模板消息
    pay_order_info.prepay_id = pay_info['prepay_id']
    db.session.add(pay_order_info)
    db.session.commit()

    reqs['data']['pay_info'] = pay_info
    return jsonify(reqs)

# 解析微信回调


@route_api.route("/order/callback", methods=["POST"])
def orderCallback():
    result_data = {
        'return_code': 'SUCCESS',
        'return_msg': 'OK'
    }
    header = {'Content-Type': 'application/xml'}
    config_mina = app.config['MIN_APP']
    target_wechat = WeChatService2(merchant_key=config_mina['paykey'])
    callback_data = target_wechat.xml_to_dict2(request.data)
    app.logger.info(callback_data)

    sign = callback_data['sign']
    callback_data.pop('sign')
    gene_sign = target_wechat.create_sign2(callback_data)
    app.logger.info(gene_sign)

    if sign != gene_sign:
        result_data['return_code'] = result_data['return_msg'] = 'FAIL'
        return target_wechat.dict_to_xml2(result_data), header

    if callback_data['result_code'] != 'SUCCESS':
        result_data['return_code'] = result_data['return_msg'] = 'FAIL'
        return target_wechat.dict_to_xml2(result_data), header

    order_sn = callback_data['out_trade_no']
    pay_order_info = PayOrder.query.filter_by(order_sn=order_sn).first()

    if not pay_order_info:
        result_data['return_code'] = result_data['return_msg'] = 'FAIL'
        return target_wechat.dict_to_xml2(result_data), header

    if int(pay_order_info.total_price * 100) != int(callback_data['total_fee']):
        result_data['return_code'] = result_data['return_msg'] = 'FAIL'
        return target_wechat.dict_to_xml2(result_data), header

    if pay_order_info.status == 1:
        return target_wechat.dict_to_xml2(result_data), header

    target_pay = PayServce2()
    target_pay.orderSuccess2(pay_order_id=pay_order_info.id, params={"pay_sn": callback_data['transaction_id']})
    # 将微信回调的结果写入记录表
    target_pay.addPayCallbackData2(pay_order_id=pay_order_info.id, data=request.data)

    return target_wechat.dict_to_xml2(result_data), header
