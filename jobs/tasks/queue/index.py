from common.models.queue.QueueList import QueueList
from common.models.food.Food import Food
from common.models.food.FoodSaleChangelog import FoodSaleChangeLog
from common.models.pay.PayOrderItem import PayOrderItem
from common.models.pay.PayOrder import PayOrder
from common.models.menber.Oauth_member_bind import OauthMemberBind
from common.libs.Helper import getCurrentDate
from common.libs.pay.WeChatService import WeChatService
from application import app,db
import json,requests,datetime
from sqlalchemy import func


"""
python manager.py runjob -m queue/index
"""

class JobTask():
    def __init__(self):
        pass

    def run(self,params):
        list = QueueList.query.filter_by(status = -1).order_by(QueueList.id.asc()).limit(1).all()
        for item in list:
            if item.queue_name =='pay':
                self.handlePay(item)

            item.status = 1
            item.updated_time = getCurrentDate()
            db.session.add(item)
            db.session.commit()

    def handlePay(self,item):
        data = json.loads(item.data)
        # 判断data里有没有member_id，pay_order_id
        if 'member_id' not in data or 'pay_order_id' not in data:
            return False

        oauth_bind_info = OauthMemberBind.query.filter_by(member_id = data['member_id']).first()
        if not oauth_bind_info:
            return False

        pay_order_info = PayOrder.query.filter_by(id = data['pay_order_id']).first()
        if not pay_order_info:
            return False

        pay_order_items = PayOrderItem.query.filter_by(pay_order_id = pay_order_info.id).all()
        noticer_content = []
        # 更新销售总量
        if pay_order_items:
            date_from = datetime.datetime.now().strftime("%Y-%m-01 00:00:00")
            date_to = datetime.datetime.now().strftime("%Y-%m-31 23:59:59")

            for item in pay_order_items:
                tmp_food_info = Food.query.filter_by(id = item.food_id ).first()
                if not tmp_food_info:
                    continue

                noticer_content.append("%s  %s份" % (tmp_food_info.name,item.quantity) )

                # 当月数量
                tmp_stat_info = db.session.query(FoodSaleChangeLog.id,
                                                 func.sum(FoodSaleChangeLog.quantity).label("total")) \
                    .filter(FoodSaleChangeLog.food_id == item.food_id) \
                    .filter(FoodSaleChangeLog.created_time >= date_from,
                            FoodSaleChangeLog.created_time <= date_to) \
                    .group_by(FoodSaleChangeLog.id) \
                    .first()
                print("#"*50)
                print(tmp_stat_info)
                tmp_month_cont = tmp_stat_info[1] if tmp_stat_info[1] else 0

                # 总销售量
                tmp_food_info.total_count += 1
                # 月销售数量
                tmp_food_info.month_count = tmp_month_cont
                db.session.add(tmp_food_info)
                db.session.commit()


        if pay_order_info.prepay_id != "1":
            # 当prepay_id == 1表示用户接受发订阅消息
            print("skip notice~~")
            return

        # 订单号
        keyword1_val = pay_order_info.order_number
        # 点餐内容
        keyword2_val = "、".join(noticer_content)
        # 消费金额
        keyword3_val = "总价：" + str(pay_order_info.total_price)
        # if pay_order_info.express_info:
        #     express_info = json.loads(pay_order_info.express_info)
        #     keyword3_val += "快递信息：" + str(express_info['address'])

        target_wechat = WeChatService()
        access_token = target_wechat.getAccessToken()
        headers = {'Content-Type': 'application/json'}
        url = "https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token=%s" % access_token

        params = {
            "touser": oauth_bind_info.openid,
            "template_id": "6Vlz_bsEJuV74r-Wz6pKCxOXvmlX38FR1QZVMWxvZV0",
            "page": "pages/my/order_list",
            "data": {
                "character_string1": {
                    "value": keyword1_val
                },
                "thing2": {
                    "value": keyword2_val
                },
                "amount10": {
                    "value": keyword3_val
                }
            }
        }
        print(params)
        r = requests.post(url=url, data=json.dumps(params).encode('utf-8'), headers=headers)
        r.encoding = "utf-8"
        print(r.text)
        return True


        # # 备注
        # thing5 = pay_order_info.note if pay_order_info.note else '无'
        # # 点餐内容
        # thing1 = "、".join(noticer_content)
        # # 消费金额
        # thing2 = "总价："+str(pay_order_info.total_price)
        # # 订单号
        # thing3 = str(pay_order_info.order_number)
        # # 配送地址
        # thing4 = ''
        #
        # target_wechat = WeChatService()
        # access_token = target_wechat.getAccessToken()
        #
        # url = "https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token=%s" % access_token
        # headers = {'Content-Type': 'application/json'}
        #
        # params = {
        #     "touser": oauth_bind_info.openid,
        #     "template_id": "0TGPtYJ84Wi4iTzr8xdNmR_pYxPuvYAeELqF45UPuaU",
        #     "page": "pages/my/order_list",
        #     "form_id": pay_order_info.prepay_id,
        #     "data": {
        #         "thing5": {
        #             "value": thing5
        #         },
        #         "thing1": {
        #             "value": thing1
        #         },
        #         "thing2": {
        #             "value": thing2
        #         },
        #         "thing3": {
        #             "value": thing3
        #         },
        #         "thing4": {
        #             "value": thing4
        #         }
        #     }
        # }
        # print()
        # r = requests.post( url= url,data=json.dumps( params ),headers=headers)
        # r.elapsed = 'utf-8'
        # print(r.text)
        # return True



