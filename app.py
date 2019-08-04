from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=['GET'])
def handle_get_index():
    return render_template('index.html')


@app.route('/chpass', methods=['GET'])
def handle_get_chpass():
    return render_template('chpass.html')
