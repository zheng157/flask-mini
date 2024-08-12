import os,stat,uuid
from application import app,db
from werkzeug.utils import secure_filename
from common.libs.Helper import getCurrentDate
from common.models.Images import Image


class UploadService():
    @staticmethod
    def uploadByFile(file):
        config_upload = app.config['UPLOAD']
        reqs = {'code': 200, 'msg': '操作成功', 'data': {}}
        ext = secure_filename(file.filename)
        # app.logger.info(filename)
        # 后缀名ext，rsplit 切割
        # ext = filename.rsplit('.', 1)[1]

        app.logger.info("*" * 50)
        app.logger.info(ext)

        if ext not in config_upload['ext']:
            reqs['code'] = -1
            reqs['msg'] = '不允许的扩展类型文件'
            return reqs
        # 目录 root_path
        root_path = app.root_path + config_upload['prefix_path']
        # 文件名称file_dir
        file_dir = getCurrentDate("%Y%m%d")
        # 时间目录save_dir
        save_dir = root_path + file_dir
        # 判断目录是否存在
        if not os.path.exists(save_dir):
            # 创建
            os.mkdir(save_dir)
            os.chmod(save_dir, stat.S_IRWXU | stat.S_IXGRP | stat.S_IRWXO)
        # 文件名file_mane
        file_name = str(uuid.uuid4()).replace('-', '') + '.' + ext


        # app.logger.info(root_path)
        # app.logger.info(save_dir)
        # app.logger.info(file_name)

        # 储存file.save
        app.logger.info("保存路径：{}".format(save_dir))
        file.save( "{0}/{1}".format( save_dir,file_name ) )

        model_image = Image()
        model_image.file_key = file_dir + '/' + file_name
        model_image.created_time = getCurrentDate()
        db.session.add(model_image)
        db.session.commit()

        reqs['data'] = {
            'file_key': model_image.file_key
        }
        return reqs



