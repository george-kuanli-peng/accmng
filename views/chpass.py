from flask import Blueprint, render_template, request
import json


bp = Blueprint('chpass', __name__, url_prefix='/chpass')


@bp.route('/', methods=['GET'])
def handle_get():
    return render_template('chpass.html')


@bp.route('/', methods=['POST'])
def handle_post():
    try:
        _validate()
    except (ValueError, KeyError) as err:
        return str(err)

    return '密碼修改完成'


def _validate():
    if not request.form['username']:
        raise ValueError('使用者名稱輸入錯誤')

    if not request.form['pass_orig']:
        raise ValueError('目前密碼輸入錯誤')

    if not request.form['pass_new']:
        raise ValueError('新密碼輸入錯誤')

    if request.form['pass_new'] != request.form['pass_confirm']:
        raise ValueError('新密碼輸入不一致')
