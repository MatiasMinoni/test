from sys import stdout
from typing import Dict, List
from app.database.models.shortener import Shortener
from core.webs.web_controller import ChollosWebController
from core.bot_service import BotServiceController
from flask import request, make_response, jsonify
from app.api.v1.auth import ApiAuth
from flask import Blueprint, request

app = Blueprint('api', __name__, template_folder='templates', static_folder='static', static_url_path='/user/static/')

bot_service : BotServiceController = BotServiceController
chollos_web_controller : ChollosWebController = ChollosWebController 


def set_services(services: Dict):
    global bot_service, chollos_web_controller

    bot_service = services['bot_service']
    chollos_web_controller = services['chollos_web_controller']

@app.route('/api/get_chollos', methods=['GET'])
def get_chollos():
    auth = ApiAuth()

    if not auth.validate(request.headers):
        return make_response(jsonify(status="error", msg="Invalid access token!"), 404)

    params = request.args.get('name', 'all').split(',')
    filter = request.args.get('filter', 'new')

    if not filter.lower() in ['new', 'popular', 'featured']:
        filter = 'new'

    if len(params) == 1:
        params = params[0]
    try:
        response = chollos_web_controller.get_web_chollos(params, filter=filter)
    except:
        return make_response(jsonify(status="error", msg="Server error, please try again later!"), 500)

    if response is not None:
        return make_response(jsonify(status="success", data=response), 200)

    return make_response(jsonify(status="error", msg="Please check your params and try again!"), 404)

@app.route('/api/get_bots', methods=['GET'])
def get_bots():
    auth = ApiAuth()

    if not auth.validate(request.headers):
        return make_response(jsonify(status="error", msg="Invalid access token!"), 404)
    try:
        response = bot_service.get_active_running_bots()
        return make_response(jsonify(status="success", data=response), 200)
    except:
        return make_response(jsonify(status="error", msg="Server error, please try again later!"), 500)

@app.route('/api/post_chollo', methods=['POST'])
def post_chollo():
    auth = ApiAuth()
    if not auth.validate(request.headers):
        return make_response(jsonify(status="error", msg="Invalid access token!"), 404)
    MIN_SIZE = 1
    if request.is_json and len(list(((data:=request.get_json())).keys())) >= MIN_SIZE:
        bot_id = data.pop('bot_id')
        item = data.pop('item')
        item['bot_id'] = bot_id
        if bot_id:
            bot = bot_service.get_bot_by_api(bot_id)
            if bot:
                status = bot.send_message_by_api(item)
                if status:
                    return make_response(jsonify(status="success"), 200)
                else:
                    return make_response(jsonify(status="error", msg="Bad payload format"), 400)
    return make_response(jsonify(status="error", msg="Incorrect data type!"), 415)

@app.route('/api/get_user_in_raffle', methods=['GET'])
def check_user_in_url():
    auth = ApiAuth()
    if not auth.validate(request.headers):
        return make_response(jsonify(status="error", msg="Invalid access token!"), 404)
    
    user_id = request.args.get('user_id')
    uuid = request.args.get('uuid')
    if user_id and uuid:
        try:
            response = bot_service.check_user_in_raffle(user_id, uuid)
            if response:
                return make_response(jsonify(status="success"), 200)
        except:
            return make_response(jsonify(status="error", msg="Server error, please try again later!"), 500)
    return make_response(jsonify(status="error", msg="Incorrect data type!"), 415)

@app.route('/api/add_url', methods=['POST'])
def add_url():
    auth = ApiAuth()
    if not auth.validate(request.headers):
        return make_response(jsonify(status="error", msg="Invalid access token!"), 404)
    if request.is_json and len(list(((data:=request.get_json())).keys())) >= 1:
        if data:
            shortener_service = Shortener(bot_service.database)
            try:
                response = shortener_service.add_url(data)
                if response:
                    payload = {'url': response['data']['url'] if isinstance(response, dict) else response}
                    return make_response(jsonify(status="success", data=payload), 200)
            except:
                return make_response(jsonify(status="error", msg="Server error, please try again later!"), 500)
    return make_response(jsonify(status="error", msg="Incorrect data type!"), 415)