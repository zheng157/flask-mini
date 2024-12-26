from flask import request,g
from application import db
from common.models.loh.AppAccesslog import AppAccessLog
from common.models.loh.AppErrorlog import AppErrorLog
import json
from common.libs.Helper import getCurrentDate




class LogService:

    @staticmethod
    def addAccesslog():
        target = AppAccessLog()
        target.target_url =request.url #取访问的url
        target.referer_url =request.referrer #取当前访问的refer
        target.ip = request.remote_addr #取当前ip
        target.query_params = json.dumps(request.values.to_dict()) #取当前请求方式
        if 'current_user' in g and g.current_user is not None:
            target.uid = g.current_user.uid  #取当前uid
        target.ua = request.headers.get("User-Agent") #取当前访问ua
        target.created_time = getCurrentDate() #取当前访问的时间


        db.session.add( target)
        db.session.commit()
        return True


    @staticmethod
    def addErrorlog(content):
        target = AppErrorLog()
        target.target_url =request.url #取访问的url
        target.referer_url =request.referrer #取当前访问的refer
        target.query_params = json.dumps(request.values.to_dict())  # 取当前请求方式
        target.content = content

        target.created_time = getCurrentDate()  # 取当前访问的时间

        db.session.add(target)
        db.session.commit()
        return True




