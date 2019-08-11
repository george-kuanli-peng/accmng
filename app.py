from flask import Flask, render_template

import views.chpass
import views.forgotpass


app = Flask(__name__)
app.register_blueprint(views.chpass.bp)
app.register_blueprint(views.forgotpass.bp)


@app.route('/', methods=['GET'])
def handle_get_index():
    return render_template('index.html')
