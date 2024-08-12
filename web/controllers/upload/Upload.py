from flask import Blueprint,request,jsonify
from application import app,db
import json,re
from common.libs.UploadService import UploadService
from common.libs.UrlManager import UrlManager
from common.models.Images import Image



route_upload = Blueprint('upload_page',__name__)


@route_upload.route("/ueditor",methods = [ "GET","POST" ])
def ueditor():
    req = request.values
    action = req['action'] if 'action' in req else ''

    if action == 'config':
        # config_data = {}
        # "选择目录root_path方法"
        root_path = app.root_path
        # "获取config_path文件"
        config_path = '{0}/web/static/plugins/ueditor/upload_config.json'.format(root_path)

        with open(config_path, encoding='utf-8') as f:
            try:
                config_data = json.loads(re.sub(r'\/\*.*\*/', '', f.read()))
            except:
                config_data = {}
        return jsonify(config_data)

    if action == 'uploadimage':
        return uploadimage()

    if action == 'listimage':
        return listimage()

    return 'upload'


@route_upload.route('/pic',methods = [ "GET","POST" ])
def uploadpic():
    file_target = request.files
    upfile = file_target['pic'] if 'pic' in file_target else None
    callback_target = 'window.parent.upload'
    if upfile is None:
        return "<script type='text/javascript'>{0}.error('{1}')</script>".format(callback_target, "上传失败")

    ret = UploadService.uploadByFile(upfile)

    if ret['code'] != 200:
        return "<script type='text/javascript'>{0}.error('{1}')</script>".format(callback_target, "上传失败：" + ret['msg'])

    return "<script type='text/javascript'>{0}.success('{1}')</script>".format(callback_target,ret['data']['file_key'] )

def uploadimage():
    reps = {'state': 'SUCCESS',"url":'','title':'','original':''}
    # 取上传的文件类型
    file_target = request.files
    # app.logger.info(file_target)
    upfile = file_target['upfile'] if 'upfile' in file_target else None

    if upfile is None:
        reps['state'] = '上传失败'
        return jsonify(reps)

    ret = UploadService.uploadByFile(upfile)

    if ret['code'] != 200:
        reps['state'] = '上传失败' + ret['msg']
        return jsonify(reps)

    reps['url'] = UrlManager.buildImageUrl(ret['data']['file_key'])
    return jsonify(reps)


def listimage():

    reps = {'state': 'SUCCESS', "list": [], 'start': 0, 'total': 0}

    req = request.values

    start = int(req['start']) if 'start' in req else 0
    page_size = int(req['size']) if 'size' in req else 20

    query = Image.query
    if start > 0:
        query = query.filter(Image.id < start)

    list = query.order_by(Image.id.desc()).limit(page_size).all()
    images = []

    if list:
        for item in list:
            images.append({'url': UrlManager.buildImageUrl(item.file_key)})
            start = item.id
    reps['list'] = images
    reps['start'] = start
    reps['total'] = len(images)

    # list = Image.query.order_by(Image.id.desc()).offset(start).limit(page_size).all()
    # images = []
    # if list:
    #     for item in list:
    #         images.append({'utl':UrlManager.buildImageUrl(item.file_key)})


    # reps['list'] = images
    # reps['total'] = len(images)
    return jsonify( reps )







