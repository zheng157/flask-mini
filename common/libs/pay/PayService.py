import decimal,hashlib,time,random
from application import db,app
from common.models.food.Food import Food
from common.models.pay.PayOrder import PayOrder
from common.models.pay.PayOrderItem import PayOrderItem
from common.models.pay.payOrderCallbackData import PayOrderCallbackDatum
from common.libs.Helper import getCurrentDate
from common.libs.food.FoodService import FoodService
from common.models.food.FoodSaleChangelog import FoodSaleChangeLog
from common.libs.queue.QueueService import QueueService


class PayServce():
    def __init__(self):
        pass
    #  createOrder下单的方法  member_id是会员id  items是商品各种参数  params是运费
    def createOrder(self,member_id,items = None,params = None):
        reqs = {'code': 200, 'msg': '操作成功', 'data': {}}

        pay_price = decimal.Decimal(0.00)
        # items['price']是商品价格
        continue_cnt = 0
        foods_id = []
        for item in items:
            if decimal.Decimal(item['price']) < 0:
                continue_cnt += 1
                continue
            # pay_price总价格
            pay_price = pay_price + decimal.Decimal(item['price']) * int(item['number'])
            foods_id.append(item['id'])


        if continue_cnt >= len(items):
            reqs['code'] = -1
            reqs['msg'] = '商品items为空'
            return reqs
        # yun_price运费
        yun_price = params['yun_price'] if params and 'yun_price' in params else 0

        note = params['note'] if params and 'note' in params else ''
        express_address_id = params["express_address_id"] if params and "express_address_id" in params else 0
        express_info = params['express_info'] if params and 'express_info' in params else {}
        app.logger.info("*"*50)
        # app.logger.info(type(express_info))
        app.logger.info(express_address_id)
        app.logger.info("*" * 50)

        yun_price = decimal.Decimal(yun_price)
        total_price = pay_price + yun_price
        try:
            # 为了防止并发库存出问题了，我们做下selectfor update, 这里可以给大家演示下
            tmp_food_list = db.session.query(Food).filter(Food.id.in_(foods_id)).with_for_update().all()

            tmp_food_stock_mapping = {}
            for tmp_item in tmp_food_list:
                tmp_food_stock_mapping[tmp_item.id] =tmp_item.stock

            model_pay_order = PayOrder()
            model_pay_order.order_sn = self.geneOrderSn()
            model_pay_order.member_id = member_id
            model_pay_order.total_price = total_price
            model_pay_order.yun_price = yun_price
            model_pay_order.pay_price = pay_price
            model_pay_order.note = note
            model_pay_order.status = -8
            model_pay_order.express_address_id = express_address_id
            model_pay_order.express_info = express_info
            model_pay_order.express_status = -8
            model_pay_order.updated_time = model_pay_order.created_time = getCurrentDate()
            db.session.add(model_pay_order)

            for item in items:
                tmp_left_stock = tmp_food_stock_mapping[item['id']]

                if decimal.Decimal(item['id']) <0:
                    continue

                if int(item['number']) > int(tmp_left_stock):
                    return Exception('您购买的这美食太火爆了，剩余：%s,你购买%s' %(tmp_left_stock,item['number']))

                tmp_ret = Food.query.filter_by(id = item['id']).update({
                    'stock':int(tmp_left_stock) - int(item['number'])
                })

                if not tmp_ret:
                    return Exception('下单失败请重新下单')

                tmp_pay_item = PayOrderItem()
                tmp_pay_item.pay_order_id = model_pay_order.id
                tmp_pay_item.member_id = member_id
                tmp_pay_item.quantity = item['number']
                tmp_pay_item.price = item['price']
                tmp_pay_item.food_id = item['id']
                tmp_pay_item.note = note
                tmp_pay_item.updated_time = model_pay_order.created_time = getCurrentDate()
                db.session.add(tmp_pay_item)

                FoodService.setStockChangeLog(item['id'],-item['number'],'在线购买')


            db.session.commit()

            reqs['data'] = {
                'id':model_pay_order.id,
                'order_sn' : model_pay_order.order_sn,
                'total_price' : str(pay_price)
            }
        except Exception as e:
            db.session.rollback()
            print(e)
            reqs['code'] = -1
            reqs['msg'] = '下单失败，请重新下单'
            reqs['msg'] = e

        return reqs


    # 删除订单方法
    def closeOrder(self, pay_order_id = 0):
        if pay_order_id < 1:
            return False

        pay_order_info = PayOrder.query.filter_by(id  = pay_order_id,status = -8 ).first()
        if not  pay_order_info:
            return False

        pay_order_items = PayOrderItem.query.filter_by(pay_order_id = pay_order_info.id).all()
        if  pay_order_items:
            for item in pay_order_items:
                tmp_food_info = Food.query.filter_by(id =item.food_id ).first()
                if tmp_food_info:
                    tmp_food_info.stock = tmp_food_info.stock + item.quantity
                    tmp_food_info.updated_time = getCurrentDate()
                    db.session.add(tmp_food_info)
                    db.session.commit()

                    FoodService.setStockChangeLog(item.food_id,item.quantity,'订单取消')

        pay_order_info.status = 0
        pay_order_info.updated_time = getCurrentDate()
        db.session.add(pay_order_info)
        db.session.commit()

        return True


    # 支付成功后调用                         params是回调的差数
    def orderSuccess(self,pay_order_id = 0 ,params = None):
        app.logger.info(params['pay_sn']+"成功")
        try:
            pay_order_info = PayOrder.query.filter_by(id = pay_order_id).first()
            if not pay_order_info or pay_order_info.status not in [-8 , -7] :
                return True
            # pay_sn是第三方流水号
            pay_order_info.pay_sn = params['pay_sn'] if params and 'pay_sn' in params else ''
            pay_order_info.status = 1
            pay_order_info.express_status = -7
            pay_order_info.updated_time = getCurrentDate()
            pay_order_info.pay_time = getCurrentDate()
            db.session.add(pay_order_info)

            # 售卖历史记录
            pay_order_items = PayOrderItem.query.filter_by(pay_order_id=pay_order_id).all()
            for order_item in pay_order_items:
                tmp_model_sale_log = FoodSaleChangeLog()
                tmp_model_sale_log.food_id = order_item.food_id
                tmp_model_sale_log.quantity = order_item.quantity
                tmp_model_sale_log.price = order_item.price
                tmp_model_sale_log.member_id = order_item.member_id
                tmp_model_sale_log.created_time = getCurrentDate()
                db.session.add(tmp_model_sale_log)


            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return False

        # 加入通知队列，做消息提醒
        QueueService.addQueue('pay',{
            "member_id":pay_order_info.member_id,
            "pay_order_id":pay_order_info.id
        })

        app.logger.info("加入通知队列成功")
        return True


    # 写进回调记录表
    def addPayCallbackData(self,pay_order_id = 0,type = 'pay',data = ''):
        mode_callback = PayOrderCallbackDatum()
        mode_callback.pay_order_id = pay_order_id
        if type == 'pay':
            mode_callback.pay_data = data
            mode_callback.refund_data = ''
        else:
            mode_callback.pay_data = ''
            mode_callback.refund_data = data
        mode_callback.created_time = mode_callback.updated_time = getCurrentDate()
        app.logger.info("写进回调记录表成功")
        db.session.add(mode_callback)
        db.session.commit()

    # geneOrderSn生成随机订单号
    def geneOrderSn(self):
        m = hashlib.md5()
        sn = None
        while True:
            str = "%s-%s" % (int(round(time.time()* 1000)),random.randint(1,99999999))
            m.update(str.encode('utf-8'))
            sn = m.hexdigest()
            if not PayOrder.query.filter_by(order_sn = sn ).first():
                break
        return sn

