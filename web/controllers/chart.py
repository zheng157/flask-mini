from flask import Blueprint,jsonify
from common.libs.Helper import getFormatDate
from common.models.stat.StatDailySite import StatDailySite

import datetime
route_chart = Blueprint('chart_page',__name__)


@route_chart.route('/dashboard')
def dashboard():
    now = datetime.datetime.now()
    date_before_30day = now + datetime.timedelta(days=-30)
    date_from = getFormatDate(date=date_before_30day, format="%Y-%m-%d")
    date_to = getFormatDate(date=now, format="%Y-%m-%d")

    list = StatDailySite.query.filter(StatDailySite.date >= date_from) \
        .filter(StatDailySite.date <= date_to).order_by(StatDailySite.id.asc()).all()

    reps = {'code':200,'msg':'操作成功','data':{}}

    data = {
        'categories':[],
        'series':[
            {
                "name":"会员总数",
                "data":[]
            },
            {
                "name": "订单总数",
                "data": []
            }
        ]
    }
    if list:
       for item in list:
           data['categories'].append(getFormatDate(date =item.date ,format = "%Y-%m-%d"))
           data['series'][0]['data'].append(item.total_member_count)
           data['series'][1]['data'].append(item.total_order_count)
    reps['data' ] = data

    return jsonify(reps)

@route_chart.route('/finance')
def finance():
    now = datetime.datetime.now()
    date_before_30day = now + datetime.timedelta(days=-30)
    date_from = getFormatDate(date=date_before_30day, format="%Y-%m-%d")
    date_to = getFormatDate(date=now, format="%Y-%m-%d")

    list = StatDailySite.query.filter(StatDailySite.date >= date_from) \
        .filter(StatDailySite.date <= date_to).order_by(StatDailySite.id.asc()).all()

    reps = {'code': 200, 'msg': '操作成功', 'data': {}}

    data = {
        'categories': [],
        'series': [
            {
                "name": "日营收情况",
                "data": []
            }

        ]
    }
    if list:
        for item in list:
            data['categories'].append(getFormatDate(date=item.date, format="%Y-%m-%d"))
            data['series'][0]['data'].append(float(item.total_pay_money))

            reps['data'] = data

    return jsonify(reps)

@route_chart.route('/share')
def share():
    now = datetime.datetime.now()
    date_before_30day = now + datetime.timedelta(days=-30)
    date_from = getFormatDate(date=date_before_30day, format="%Y-%m-%d")
    date_to = getFormatDate(date=now, format="%Y-%m-%d")

    list = StatDailySite.query.filter(StatDailySite.date >= date_from) \
        .filter(StatDailySite.date <= date_to).order_by(StatDailySite.id.asc()).all()

    reps = {'code': 200, 'msg': '操作成功', 'data': {}}

    data = {
        'categories': [],
        'series': [
            {
                "name": "分享次数情况",
                "data": []
            }

        ]
    }
    if list:
        for item in list:
            data['categories'].append(getFormatDate(date=item.date, format="%Y-%m-%d"))
            data['series'][0]['data'].append(float(item.total_shared_count))

            reps['data'] = data


    return jsonify(reps)