from flask import Blueprint, current_app,url_for, redirect, session, render_template
from app.database.models import Admin, Editor
from functools import wraps
from flask import g


app = Blueprint('user_api', __name__, url_prefix='/api')
db = {'db':''}

@app.route('/api/user/get_all_bots', methods=['POST'])
def get_all_bots():
    pass

@app.route('/api/user/get_all_users', methods=['POST'])
def get_all_users():
    pass

@app.route('/api/user/edit_item', methods=['POST'])
def edit_item():
    pass