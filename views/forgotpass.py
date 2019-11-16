import math
import string
import random

from flask import Blueprint, render_template, request

import libs.backends
import libs.backends.webportal
import libs.config
import libs.db
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

        if not libs.backends.auth_user_mail(username, email):
            raise ValueError('username and email not match!')

        uid = libs.db.get_uid(username)
        reset_pass_len = 6
        reset_pass = ''.join(random.choices(string.ascii_lowercase + string.digits, k=reset_pass_len))
        action_ret = libs.backends.webportal.create_user_action(
            uid=uid,
            action_type=libs.backends.webportal.UserAction.FORGOT_PASS,
            parm=reset_pass
        )
        base_url = libs.config.get_value('WEB_PORTAL', 'BASE_URL')
        libs.mail.send_msg(
            email,
            '忘記密碼',
            '重設密碼連結如下 (%d 分鐘內有效):\n' % math.floor(action_ret['valid_period']/60) +
            '%s/forgotpass/reset/uid=%d&p=%s' % (base_url, uid, reset_pass)
        )
    except (ValueError, KeyError) as err:
        raise

    return '信件己送出，請收信。如果沒收到，請試著在垃圾信件匣尋找。'
