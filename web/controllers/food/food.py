from flask import Blueprint,request,jsonify,redirect
from common.libs.Helper import ops_render,getCurrentDate,iPagination,getDictFilterField
from common.models.food.Foodcat import FoodCat
from application import db,app
from decimal import Decimal
from common.models.food.Food import Food
from common.models.food.FoodStockChangelog import FoodStockChangeLog
from common.libs.UrlManager import UrlManager
from sqlalchemy import  or_
from common.libs.food.FoodService import FoodService
route_food = Blueprint('food',__name__)


@route_food.route('/index')
def index():
    reqs_data = {}
    req = request.values
    page = int(req['p'] if ('p' in req and req['p']) else 1)
    query = Food.query

    if 'mix_kw' in req:
        rule = or_(Food.name.ilike("%{0}%".format(req['mix_kw'])), Food.tags.ilike("%{0}%".format(req['mix_kw'])))
        query = query.filter(rule)

    if 'status' in req and int(req['status']) > -1:
        query = query.filter(Food.status == int(req['status']))

    if 'cat_id' in req and int( req['cat_id'] ) > 0 :
        query = query.filter ( Food.cat_id == int( req['cat_id'] ) )

    page_params = {
        'total': query.count(),
        'page_size': app.config['PAGE_SIZE'],
        'page': page,
        'display': app.config['PAGE_DISPLAY'],
        'url': request.full_path.replace("&p={}".format(page), "")
    }
    pages = iPagination(page_params)
    offset = (page - 1) * app.config['PAGE_SIZE']
    limit = app.config['PAGE_SIZE'] * page

    list = query.order_by(Food.id.desc()).all()[offset:limit]
    cat_mapping = getDictFilterField(FoodCat,'id','id',[])

    reqs_data['list'] = list
    reqs_data['pages'] = pages
    reqs_data['search_con'] = req
    reqs_data['cat_mapping'] = cat_mapping
    reqs_data['status_mapping'] = app.config['STATUS_MAPPING']
    reqs_data['current'] = 'index'
    return ops_render('food/index.html',reqs_data)


@route_food.route('/info')
def info():
    resp_data = {}
    req = request.args
    id = int(req.get('id', 0))
    reback_url = UrlManager.buildUrl("/food/index")

    if id < 1:
        return redirect( reback_url )

    info = Food.query.filter_by(id = id).first()

    if not info:
        return redirect(reback_url)

    info_list = FoodStockChangeLog.query.filter(FoodStockChangeLog.food_id == id) \
        .order_by(FoodStockChangeLog.id.desc()).all()


    app.logger.info(info_list)
    resp_data['info'] = info
    resp_data['info_list'] = info_list
    resp_data['current'] = 'index'

    return ops_render('food/info.html',resp_data)


@route_food.route( "/set" ,methods = [ 'GET','POST'] )
def set():
    if request.method == "GET":
        reqs_data = {}
        req = request.args
        id = int( req.get('id',0) )
        info = Food.query.filter_by( id = id ).first()
        # app.logger.info(req)
        # app.logger.info(id)
        if info and info.status != 1:
            return redirect( UrlManager.buildUrl("/food/index") )

        info2 = FoodStockChangeLog()
        cat_list = FoodCat.query.all()

        reqs_data['info'] = info
        reqs_data['cat_list'] = cat_list
        reqs_data['current'] = 'index'
        return ops_render( "food/set.html" ,reqs_data)

    reqs = {'code': 200, 'msg': '操作成功~~', 'data': {}}
    req = request.values
    id = int(req['id']) if 'id' in req and req['id'] else 0
    cat_id = int(req['cat_id']) if 'cat_id' in req else 0
    name = req['name'] if 'name' in req else ''
    price = req['price'] if 'price' in req else ''
    main_image = req['main_image'] if 'main_image' in req else ''
    summary = req['summary'] if 'summary' in req else ''
    stock = int(req['stock']) if 'stock' in req else ''
    tags = req['tags'] if 'tags' in req else ''
    remark = req['remark'] if 'remark' in req else ''

    # app.logger.info(remark)
    if cat_id < 1:
        reqs['code'] = -1
        reqs['msg'] = "请选择分类~~"
        return jsonify(reqs)

    if name is None or len(name) < 1:
        reqs['code'] = -1
        reqs['msg'] = "请输入符合规范的名称~~"
        return jsonify(reqs)

    if not price or len( price ) < 1:
        reqs['code'] = -1
        reqs['msg'] = "请输入符合规范的售卖价格~~"
        return jsonify(reqs)

    price = Decimal(price).quantize(Decimal('0.00'))
    if  price <= 0:
        reqs['code'] = -1
        reqs['msg'] = "请输入符合规范的售卖价格~~"
        return jsonify(reqs)

    if main_image is None or len(main_image) < 3:
        reqs['code'] = -1
        reqs['msg'] = "请上传封面图~~"
        return jsonify(reqs)

    if summary is None or len(summary) < 3:
        reqs['code'] = -1
        reqs['msg'] = "请输入图书描述，并不能少于10个字符~~"
        return jsonify(reqs)

    if stock < 1:
        reqs['code'] = -1
        reqs['msg'] = "请输入符合规范的库存量~~"
        return jsonify(reqs)

    if tags is None or len(tags) < 1:
        reqs['code'] = -1
        reqs['msg'] = "请输入标签，便于搜索~~"
        return jsonify(reqs)



    food_info = Food.query.filter_by(id=id).first()
    before_stock = 0
    if food_info:
        model_food = food_info
        before_stock = model_food.stock
    else:
        model_food = Food()
        model_food.status = 1
        model_food.created_time = getCurrentDate()

    model_food.cat_id = cat_id
    model_food.name = name
    model_food.price = price
    model_food.main_image = main_image
    model_food.summary = summary
    model_food.stock = stock
    model_food.tags = tags
    model_food.updated_time = getCurrentDate()

    db.session.add(model_food)
    ret = db.session.commit()


    FoodService.setStockChangeLog( model_food.id,int(stock) - int(before_stock),remark )


    return jsonify(reqs)



@route_food.route('/cat')
def cat():
    reqs_data = {}
    req = request.values
    query = FoodCat.query

    if 'status' in req and int(req['status']) > -1:
        query = query.filter(FoodCat.status == int(req['status']))

    list = query.order_by(FoodCat.weight.desc(), FoodCat.id.desc()).all()

    reqs_data['list'] = list
    reqs_data['search_con'] = req
    reqs_data['status_mapping'] = app.config['STATUS_MAPPING']
    reqs_data['current'] = 'cat'

    return ops_render('food/cat.html',reqs_data)


@route_food.route( "/cat-set",methods = [ "GET","POST" ] )
def catSet():
    if request.method == "GET":
        reqs_data = {}
        req = request.args
        id = int(req.get("id", 0))
        info = None
        if id:
            info = FoodCat.query.filter_by( id = id ).first()
        reqs_data['info'] = info
        reqs_data['current'] = 'cat'
        return ops_render( "food/cat_set.html" ,reqs_data )

    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    name = req['name'] if 'name' in req else ''
    weight = int( req['weight'] ) if ( 'weight' in req  and  int( req['weight']) > 0 ) else 1

    if name is None or len( name ) < 1:
        reqs['code'] = -1
        reqs['msg'] = "请输入符合规范的分类名称"
        return jsonify( reqs )

    food_cat_info = FoodCat.query.filter_by( id = id ).first()
    if food_cat_info:
        model_food_cat = food_cat_info
    else:
        model_food_cat = FoodCat()
        model_food_cat.created_time = getCurrentDate()
    model_food_cat.name = name
    model_food_cat.weight = weight
    model_food_cat.updated_time = getCurrentDate()
    db.session.add(model_food_cat)
    db.session.commit()
    return jsonify( reqs )

@route_food.route("/cat-ops",methods = [ "POST" ])
def catOps():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    act = req['act'] if 'act' in req else ''
    if not id :
        reqs['code'] = -1
        reqs['msg'] = "请选择要操作的账号"
        return jsonify(reqs)

    if  act not in [ 'remove','recover' ] :
        reqs['code'] = -1
        reqs['msg'] = "操作有误，请重试"
        return jsonify(reqs)

    food_cat_info = FoodCat.query.filter_by( id= id ).first()
    if not food_cat_info:
        reqs['code'] = -1
        reqs['msg'] = "指定分类不存在"
        return jsonify(reqs)

    if act == "remove":
        food_cat_info.status = 0
    elif act == "recover":
        food_cat_info.status = 1

        food_cat_info.update_time = getCurrentDate()
    db.session.add( food_cat_info )
    db.session.commit()
    return jsonify(reqs)

@route_food.route('/ops',methods=['POST'])
def ops():
    reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
    req = request.values

    id = req['id'] if 'id' in req else 0
    act = req['act'] if 'act' in req else ''

    # app.logger.info(req)

    if not id:
        reqs['code'] = -1
        reqs['msg'] = '请选择要操作的账号'
        return jsonify(reqs)

    if  act not in [ 'remove','recover' ] :
        reqs['code'] = -1
        reqs['msg'] = "操作有误，请重试~~"
        return jsonify(reqs)


    user_info = Food.query.filter_by(id = id).first()
    if not user_info:
        reqs['code'] = -1
        reqs['msg'] = '美食不存在'
        return jsonify(reqs)

    if act == "remove":
        user_info.status = 0
    elif act == "recover":
        user_info.status = 1

    user_info.update_time = getCurrentDate()
    db.session.add(user_info)
    db.session.commit()
    return jsonify(reqs)






