from flask import Blueprint, render_template, request

import libs.backends
import libs.mail


bp = Blueprint('forgotpass', __name__, url_prefix='/forgotpass')


@bp.route('/', methods=['GET'])
def handle_get():
    return render_template('forgotpass.html')


@bp.route('/', methods=['POST'])
def handle_post():
    try:
        username = request.form['username']
        email = request.form['email']
        if libs.backends.auth_user_mail(username, email):
            libs.mail.send_msg(email, '忘記密碼', '忘記密碼連結')
        else:
            raise ValueError('username and email not match!')
    except (ValueError, KeyError) as err:
        return str(err)

    return '信件己送出，請收信。如果在 10 分鐘內沒收到，請試著在垃圾信件匣尋找。'
