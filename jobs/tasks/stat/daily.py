from application import app,db
from common.libs.Helper import getFormatDate,getCurrentDate
from common.models.menber.Menber import Member
from common.models.stat.StatDailySite import StatDailySite
from common.models.stat.StatDailyFood import StatDailyFood
from common.models.stat.StatDailyMember import StatDailyMember
from common.models.food.WxShareHistory import WxShareHistory
from common.models.food.FoodSaleChangelog import FoodSaleChangeLog
from common.models.pay.PayOrder import PayOrder
from sqlalchemy import func
import random,datetime


"""
python manager.py runjob -m stat/daily -a member | food | site -p 2024-01-08
"""

class JobTask():
    def __init__(self):
        pass

    def run(self,params):
        act = params['act'] if 'act' in params else ''
        date = params['param'][0] if params['param'] and len(params['param']) > 0 else getFormatDate(format = '%Y-%m-%d')

        print(params)
        print(act)
        print(date)
        # 一天的开始时间和结束时间
        date_from = date + " 00:00:00"
        date_to = date + " 23:59:59"

        func_params = {
            "act" : act,
            "date":date,
            "date_from":date_from,
            "date_to":date_to,
        }
        if not act:
            return

        # member会员统计
        if act == 'member':
            self.statMember(func_params)
        # food售卖统计
        elif act == 'food':
            self.statFood(func_params)
        # site全站统计
        elif act == 'site':
            self.stat(func_params)

        elif act == 'test':
            self.test()

    '''
    会员统计
    '''
    def statMember(self,params):
        act = params['act']
        date = params['date']
        date_from = params['date_from']
        date_to = params['date_to']

        print("act:{0},from:{1},to:{2}".format(act,date_from,date_to))
        # import warnings
        # warnings.filterwarnings('ignore', '.*Incorrect string value.*')
        member_list = Member.query.all()
        if not member_list:
            print('无成员列表')
            return

        for member_info in member_list:
            tmp_stat_member = StatDailyMember.query.filter_by(date = date,member_id = member_info.id ).first()
            if tmp_stat_member:
                tmp_model_stat_member = tmp_stat_member
            else:
                tmp_model_stat_member = StatDailyMember()
                tmp_model_stat_member.member_id = member_info.id
                tmp_model_stat_member.date = date
                tmp_model_stat_member.created_time = getCurrentDate()




            # tmp_stat_pay 一天总付款金额
            tmp_stat_pay = db.session.query(func.sum(PayOrder.total_price).label("total_pay_money")) \
                .filter(PayOrder.member_id == member_info.id, PayOrder.status == 1) \
                .filter(PayOrder.created_time >= date_from, PayOrder.created_time <= date_to).first()


            # tmp_stat_share_count = db.session.query(func.count(WxShareHistory.id)) \
            #     .join(PayOrder, WxShareHistory.member_id == PayOrder.member_id) \
            #     .filter(PayOrder.member_id == member_info.id) \
            #     .filter(PayOrder.created_time >= date_from, PayOrder.created_time <= date_to).first()

            # tmp_stat_pay = db.session.query(func.sum(PayOrder.total_price).label("total_pay_money")) \
            #     .filter(PayOrder.member_id == member_info.id, PayOrder.status == 1) \
            #     .filter(PayOrder.created_time >= date_from, PayOrder.created_time <= date_to).first()

            # tmp_stat_share_count 一天总分享
            tmp_stat_share_count = WxShareHistory.query.filter(PayOrder.member_id == member_info.id) \
                .filter(PayOrder.created_time >= date_from, PayOrder.created_time <= date_to).count()

            print(tmp_stat_pay)
            print(tmp_stat_share_count)
            tmp_model_stat_member.total_shared_count = tmp_stat_share_count
            tmp_model_stat_member.total_pay_money = tmp_stat_pay[0] if tmp_stat_pay[0] else 0.00

            '''
            为了测试效果模拟数据
            '''
            tmp_model_stat_member.total_shared_count = random.randint(50, 100)
            tmp_model_stat_member.total_pay_money = random.randint(1000, 1010)

            tmp_model_stat_member.updated_time = getCurrentDate()
            db.session.add(tmp_model_stat_member)
            db.session.commit()

        return True

    '''
    Food统计
    '''
    def statFood(self, params):
        act = params['act']
        date = params['date']
        date_from = params['date_from']
        date_to = params['date_to']

        print("act:{0},from:{1},to:{2}".format(act, date_from, date_to))

        stat_food_list = db.session.query(FoodSaleChangeLog.food_id , func.sum(FoodSaleChangeLog.quantity ).label("total_count")
                         , func.sum(FoodSaleChangeLog.price ).label("total_pay_money" ))\
            .filter(FoodSaleChangeLog.created_time >= date_from , FoodSaleChangeLog.created_time <= date_to)\
            .group_by(FoodSaleChangeLog.food_id).all()

        if not stat_food_list:
            print('无 data')
            return

        for item in stat_food_list:
            tmp_food_id = item[0]
            tmp_stat_food = StatDailyFood.query.filter_by(date=date, food_id = tmp_food_id).first()
            if tmp_stat_food:
                tmp_model_stat_food = tmp_stat_food
            else:
                tmp_model_stat_food = StatDailyFood()
                tmp_model_stat_food.food_id = tmp_food_id
                tmp_model_stat_food.date = date
                tmp_model_stat_food.created_time = getCurrentDate()



            tmp_model_stat_food.total_count = item[1]
            tmp_model_stat_food.total_pay_money = item[2]

            '''
            为了测试效果模拟数据
            '''
            tmp_model_stat_food.total_shared_count = random.randint(50, 100)
            tmp_model_stat_food.total_pay_money = random.randint(1000, 1010)

            tmp_model_stat_food.updated_time = getCurrentDate()
            db.session.add(tmp_model_stat_food)
            db.session.commit()

        return True

    '''
    site统计
    '''
    def stat(self,params):
        act = params['act']
        date = params['date']
        date_from = params['date_from']
        date_to = params['date_to']

        print("act:{0},from:{1},to:{2}".format(act,date_from,date_to))

        # 全站统计
        stat_pay = db.session.query(func.sum(PayOrder.total_price).label("total_pay_money"))\
            .filter(PayOrder.status == 1)\
            .filter(PayOrder.created_time >= date_from,PayOrder.created_time <= date_to ).first()

        # 会员统计
        stat_member_count = Member.query.count()

        # 新增会员统计
        stat_new_member_count = Member.query.filter(Member.created_time >= date_from,Member.created_time <= date_to ).count()

        # 总的订单数量
        stat_order_count = PayOrder.query.filter_by(status = 1 )\
            .filter(PayOrder.created_time >= date_from,PayOrder.created_time <= date_to ).count()

        # 分享总数量
        stat_share_count = WxShareHistory.query.filter(WxShareHistory.created_time >= date_from,WxShareHistory.created_time <= date_to ).count()

        tmp_stat_site = StatDailySite.query.filter_by(date = date).first()
        if tmp_stat_site:
            tmp_model_stat_site = tmp_stat_site
        else:
            tmp_model_stat_site = StatDailySite()
            tmp_model_stat_site.date = date
            tmp_model_stat_site.created_time = getCurrentDate()

        tmp_model_stat_site.total_pay_money = stat_pay[0] if stat_pay[0] else 0.00
        tmp_model_stat_site.total_new_member_count = stat_new_member_count
        tmp_model_stat_site.total_member_count = stat_member_count
        tmp_model_stat_site.total_order_count = stat_order_count
        tmp_model_stat_site.total_shared_count = stat_share_count
        tmp_model_stat_site.updated_time = getCurrentDate()

        '''
        为了测试效果模拟数据
        '''
        tmp_model_stat_site.total_pay_money = random.randint(1000, 1010)
        tmp_model_stat_site.total_new_member_count = random.randint(50, 100)
        tmp_model_stat_site.total_member_count += tmp_model_stat_site.total_new_member_count
        tmp_model_stat_site.total_order_count = random.randint(900, 1000)
        tmp_model_stat_site.total_shared_count = random.randint(1000, 2000)

        db.session.add(tmp_model_stat_site)
        db.session.commit()


        return True

    # 过去30天全站统计
    def test(self):
        now = datetime.datetime.now()
        for i in reversed(range(1,30)):
            date_before = now + datetime.timedelta(days =- i)
            date = getFormatDate(date = date_before,format = "%Y-%m-%d")
            tmp_params = {
                "act" : "test",
                "date" : date,
                "date_from" : date + " 00:00:00",
                "date_to" : date + " 23:59:59",
            }
            self.statFood(tmp_params)
            self.statMember(tmp_params)
            self.stat(tmp_params)


