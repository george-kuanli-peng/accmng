from flask import Blueprint, render_template, request

import libs.backends
import libs.db


bp = Blueprint('chpass', __name__, url_prefix='/chpass')


@bp.route('/', methods=['GET'])
def handle_get():
    return render_template('chpass.html')


@bp.route('/', methods=['POST'])
def handle_post():
    try:
        username = request.form['username']
        pass_orig = request.form['pass_orig']
        pass_new = request.form['pass_new']
        pass_confirm = request.form['pass_confirm']

        _validate(username, pass_orig, pass_new, pass_confirm)
        libs.db.apply_user(username, password=pass_new)
        libs.backends.apply_user(username, password=pass_new)
    except (ValueError, KeyError) as err:
        return str(err)

    return '密碼修改完成'


def _validate(username: str, pass_orig: str, pass_new: str, pass_confirm: str):
    if not username:
        raise ValueError('使用者名稱輸入錯誤')

    if not libs.backends.auth_user_pass(username, pass_orig):
        raise ValueError('目前密碼輸入錯誤')

    if not pass_new:
        raise ValueError('新密碼輸入錯誤')

    if pass_new != pass_confirm:
        raise ValueError('新密碼輸入不一致')
