import datetime
from common.models.pay.PayOrder import PayOrder
from common.models.pay.PayOrderItem import PayOrderItem
from common.libs.pay.PayService import PayServce
from application import app,db
"""
python manager.py runjob-m pay/index
"""
# 定时器实现自动取消订单
class JobTask():
    def __init__(self):
        pass

    def run(self,params):

        now = datetime.datetime.now()
        data_before_30min = now + datetime.timedelta(minutes=-30)
        list = PayOrder.query.filter_by(status = -8)\
            .filter(PayOrder.created_time <= data_before_30min.strftime("%Y-%m-%d %H:%M:%S")).all()
        print(data_before_30min)
        if not list:
            print("没有 data")
            return

        pay_target = PayServce()
        for item in list:
            pay_target.closeOrder(pay_order_id =item.id )

        print("成功取消")
        return





