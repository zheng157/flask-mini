from flask import Blueprint
route_api = Blueprint('route_api',__name__)
from web.controllers.api.Member import *
from web.controllers.api.food import *
from web.controllers.api.Cart import *
from web.controllers.api.Order import *
from web.controllers.api.My import *
from web.controllers.api.Address import *

@route_api.route('/')
def index():
    return "Mina api v1.0"