from web.controllers.api import route_api
from flask import request,jsonify,g
from common.libs.UrlManager import UrlManager
from common.models.food.Foodcat import FoodCat
from common.models.food.Food import Food
from sqlalchemy import  or_
from common.libs.Helper import  getDictFilterField,getCurrentDate,selectFilterObj
from common.models.menber.MenberCart import MemberCart
from common.models.menber.MemberComments import MemberComment
from common.models.menber.Menber import Member
from application import app,db

@route_api.route('/food/index')
def food_index():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    # 查询FoodCat表里面status是不是存在的，1存在，0不存在 以weight字段倒序排。
    cat_list = FoodCat.query.filter_by(status = 1).order_by( FoodCat.weight.desc())
    data_cat_list = []
    data_cat_list.append({
        "id":0,
        "name": "全部"
    })

    if cat_list:
        for item in cat_list:
            tmp_data = {
                "id": item.id,
                "name": item.name
            }
            data_cat_list.append(tmp_data)

    reqs['data']['cat_list'] = data_cat_list

    food_list = Food.query.filter_by(status=1) \
        .order_by(Food.main_image.desc(),Food.id.desc()).limit(3).all()

    data_food_list = []
    if food_list:
        for i in food_list:
            tmp_data = {
                "id": i.id,
                "pic_url": UrlManager.buildImageUrl(i.main_image )
            }
            data_food_list.append(tmp_data)

    reqs['data']['banner_list'] = data_food_list


    return jsonify(reqs)


@route_api.route('/food/search')
def food_search():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    cat_id = int(req['cat_id']) if 'cat_id' in req else 0
    p = int(req['p']) if 'p' in req else 0
    mix_kw = req['mix_kw'] if 'mix_kw' in req else ''
    if p < 1:
        p = 1

    query = Food.query.filter_by(status = 1)
    page_size = 6
    offset = (p-1) * page_size


    if cat_id > 0 :
        query = query.filter ( Food.cat_id == cat_id )

    if mix_kw:
        rule = or_(Food.name.ilike("%{0}%".format(mix_kw)), Food.tags.ilike("%{0}%".format(mix_kw)))
        query = query.filter(rule)

    food_list = query.order_by(Food.total_count.desc(),
                               Food.id.desc()).offset(offset).limit(page_size).all()

    data_food = []

    if food_list:
        for i in food_list:
            tmp = {
                'id': i.id,
                "name":i.name,
                "price":str(i.price),
                "min_price":str(i.price),
                "pic_url":UrlManager.buildImageUrl(i.main_image)
            }
            data_food.append(tmp)

    reqs['data']['list'] = data_food
    reqs['data']['has_more'] = 0 if len(data_food) < page_size else 1

    return jsonify(reqs)

@route_api.route('/food/info')
def food_info():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    id = int(req['id']) if 'id' in req else 0
    # app.logger.info(id)
    food_info = Food.query.filter_by(id = id).first()


    if not food_info or not Food.status:
        reqs['code'] =-1
        reqs['msg'] = '美食已下架'
        return jsonify(reqs)

    member_info = g.member_info
    cart_number = 0
    if member_info:
        cart_number = MemberCart.query.filter_by(member_id=member_info.id).count()

    # app.logger.info(type(main_image))
    reqs['data']['info'] = {
        "id": food_info.id,
        "name": food_info.name,
        "summary": food_info.summary,
        "total_count": food_info.total_count,
        "comment_count": food_info.comment_count,
        'main_image': UrlManager.buildImageUrl(food_info.main_image),
        "price": str(food_info.price),
        "stock": food_info.stock,
        "pics": [UrlManager.buildImageUrl(food_info.main_image)]
    }

    reqs['data']['cart_number'] = cart_number

    return jsonify(reqs)

@route_api.route('/food/omments',methods=[ "POST"])
def food_omments():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values
    id = int(req['id']) if 'id' in req else 0


    query = MemberComment.query.filter(MemberComment.food_ids.ilike('%_{0}%'.format(id)))
    list = query.order_by(MemberComment.id.desc()).limit(5).all()

    # app.logger.info(list)
    data_list = []
    if list:
        # 取会员信息
        member_map = getDictFilterField(Member,Member.id,'id',selectFilterObj(list,'member_id'))
        for item in list:
            # 判断会员信息会员信息有没有
            if item.member_id not in member_map:
                continue
            tmp_member_info = member_map[item.member_id]
            tmp_data = {
                "score": item.score_desc,
                "date": item.created_time.strftime("%Y-%m-%d %H:%M:%S"), #从数据库里合时间出来，然后转格式
                "content": item.content,
                "user": {
                    "avatar_url": tmp_member_info.avatar,
                    "nickname": tmp_member_info.nickname
                }
            }

            data_list.append(tmp_data)

    reqs['data']['list']= data_list
    # count总数
    reqs['data']['count']= query.count()
    return jsonify(reqs)


