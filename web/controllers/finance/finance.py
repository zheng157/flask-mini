import json

from flask import Blueprint,request,redirect,jsonify
from common.libs.Helper import ops_render,iPagination,selectFilterObj,getDictFilterField,getDictListFilterField,getCurrentDate
from common.models.pay.PayOrder import PayOrder
from common.models.pay.PayOrderItem import PayOrderItem
from common.models.menber.Menber import Member
from common.models.food.Food import Food
from common.libs.UrlManager import UrlManager
from application import app,db
from sqlalchemy import func

route_finance = Blueprint('finance',__name__)


@route_finance.route('/account')
def account():
    resp_data = {}
    req = request.values
    page = int(req['p'] if ('p' in req and req['p']) else 1)

    query = PayOrder.query.filter_by( status = 1 )

    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }

    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']

    list = query.order_by(PayOrder.id.desc()).offset(offset).limit(app.config['PAGE_SIZE']).all()

    # 总收款金额
    # stat_info = db.session.query(PayOrder.status,func.sum(PayOrder.total_price).label("total")).filter(PayOrder.status == 1).group_by(PayOrder.status).first()
    stat_info = db.session.query(func.sum(PayOrder.total_price).label("total")).filter(PayOrder.status == 1).first()

    app.logger.info("*"*50)
    app.logger.info(stat_info[0])
    app.logger.info(type(stat_info))
    app.logger.info("*" * 50)


    resp_data['list'] = list
    resp_data['pages'] = pages
    resp_data['stat_info'] = stat_info[0] if stat_info[0] else 0.00
    resp_data['current'] = 'account'
    return ops_render('finance/account.html',resp_data)


@route_finance.route('/index')
def index():
    resp_data = {}
    req = request.values
    page = int(req['p'] if ('p' in req and req['p']) else 1)
    query = PayOrder.query
    # app.logger.info(page)

    # 判断PayOrder表里的status是不是 >= -8
    if 'status' in req and int(req['status']) >= -8:
        query = query.filter(PayOrder.status == int(req['status']))

    # 分页
    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }
    # 分页
    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']
    # 在PayOrder表里id倒序
    pay_list = query.order_by(PayOrder.id.desc()).offset(offset).limit(app.config['PAGE_SIZE']).all()

    data_list = []
    if pay_list:
        pay_order_ids = selectFilterObj(pay_list,'id')
        pay_order_items_map = getDictListFilterField(PayOrderItem,PayOrderItem.pay_order_id,'pay_order_id',pay_order_ids)

        food_mapping = {}
        if pay_order_items_map:
            food_ids = []
            for item in pay_order_items_map:
                tmp_food_ids = selectFilterObj(pay_order_items_map[item],'food_id')
                tmp_food_ids = {}.fromkeys(tmp_food_ids).keys()
                food_ids = food_ids + list(tmp_food_ids)

                # food_ids里面会有重复的，要去重
                food_mapping = getDictFilterField(Food, Food.id, "id", food_ids)

        for item in pay_list:
            tmp_data = {
                "id": item.id,
                # 状态
                "status_desc": item.status_desc,
                # 订单编号
                "order_number": item.order_number,
                # 价格
                "price": item.total_price,
                # 支付时间
                "pay_time": item.pay_time,
                # 创建时间
                "created_time": item.created_time.strftime("%Y%m%d%H%M%S")
            }
            # 名字 + 数量
            tmp_foods = []
            tmp_order_items = pay_order_items_map[item.id]
            for tmp_order_item in tmp_order_items:
                tmp_food_info = food_mapping[ tmp_order_item.food_id ]
                tmp_foods.append({
                    # 名字
                    'name':tmp_food_info.name,
                    # 数量
                    'quantity':tmp_order_item.quantity

                })
                # 把名字和数量加进tmp_data里
                tmp_data['foods'] = tmp_foods
                data_list.append(tmp_data)

    resp_data['list'] = data_list
    resp_data['pages'] = pages
    resp_data['search_con'] = req
    resp_data['pay_status_mapping'] = app.config['PAY_STATUS_MAPPING']
    resp_data['current'] = 'index'


    return ops_render('finance/index.html',resp_data)


@route_finance.route('/pay-info')
def pay_info():
    resp_data = {}
    req = request.values
    id = int(req['id']) if 'id' in req else 0

    # 返回主页
    reback_url = UrlManager.buildUrl("/finance/index")

    if id < 1:
        return redirect(reback_url)

    # PayOrder表
    pay_order_info = PayOrder.query.filter_by(id = id).first()
    if not pay_order_info:
        return redirect(reback_url)

    # Member表
    member_info = Member.query.filter_by(id = pay_order_info.member_id).first()
    if not member_info:
        return redirect(reback_url)

    # PayOrderItem表
    order_item_list = PayOrderItem.query.filter_by(pay_order_id = pay_order_info.id).all()
    data_order_item_list = []
    if order_item_list:
        food_map_ids = selectFilterObj(order_item_list,'food_id')
        food_map = getDictFilterField(Food,Food.id,'id',food_map_ids)


        for item in order_item_list:
            tmp_food_inst = food_map[item.food_id]
            tmp_data = {
                # 数量
                "quantity":item.quantity,
                # 价格
                "price":item.price,
                # 菜名
                "name":tmp_food_inst.name,
            }

            data_order_item_list.append(tmp_data)

    app.logger.info(data_order_item_list)

    address_info = {}
    if pay_order_info.express_info:
        a = pay_order_info.express_info.replace("'", "\"")
        address_info = json.loads(a)

    resp_data['pay_order_info'] = pay_order_info
    resp_data['pay_order_items'] = data_order_item_list
    resp_data['member_info'] = member_info
    resp_data['address_info'] = address_info
    resp_data['current'] = 'index'
    return ops_render('finance/pay_info.html',resp_data)


@route_finance.route('/ops',methods = [ 'POST'])
def ops():
    resp = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    id = req['id'] if 'id' in req else 0
    act = req['act'] if 'act' in req else ''

    pay_order_info = PayOrder.query.filter_by(id = id ).first()

    if not pay_order_info:
        resp['code'] = -1
        resp['msg'] = "系统繁忙。请稍后再试~~"
        return jsonify(resp)


    if act == 'express':
        pay_order_info.express_status = -6
        pay_order_info.updated_time = getCurrentDate()
        db.session.add(pay_order_info)
        db.session.commit()


    return jsonify(resp)


