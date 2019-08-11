from flask import Blueprint, render_template


bp = Blueprint('forgotpass', __name__, url_prefix='/forgotpass')


@bp.route('/', methods=['GET'])
def handle_get():
    return render_template('forgotpass.html')


@bp.route('/', methods=['POST'])
def handle_post():
    pass
