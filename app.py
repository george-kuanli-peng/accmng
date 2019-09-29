import argparse
import os

from flask import Flask, render_template
import werkzeug.exceptions

import libs.config
import libs.db
import views.chpass
import views.forgotpass


DEFAULT_PORT = 3000

app = Flask(__name__)
app.register_blueprint(views.chpass.bp)
app.register_blueprint(views.forgotpass.bp)


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, werkzeug.exceptions.HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    try:
        code = e.code
    except AttributeError:
        code = 500
    return render_template("error_generic.html", e=e), code


@app.route('/', methods=['GET'])
def handle_get_index():
    return render_template('index.html')


def main(config_file: str):
    # read config
    config_path_candidates = [
        config_file,
        os.path.join(os.getcwd(), config_file),
        os.path.join(os.path.dirname(__file__), config_file)
    ]
    for config_path_c in config_path_candidates:
        if os.path.isfile(config_path_c):
            libs.config.init_config(config_path_c)
            break
    else:
        raise Exception('No config file found!')

    # init DB
    libs.db.init_db()

    # start Web portal
    try:
        port = libs.config.get_value('WEB_PORTAL', 'PORT')
    except (KeyError, TypeError):
        port = DEFAULT_PORT
    app.run('0.0.0.0', port=port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str,
                        default='config.ini',
                        help='Configuration file path')

    args = parser.parse_args()
    main(config_file=args.config_file)
