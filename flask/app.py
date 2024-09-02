from flask import Flask, Blueprint, jsonify, request
from flask_restful import Api, Resource
import time
import socket
from os import environ
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

api = Blueprint('api', __name__, url_prefix='/')
api_v1 = Blueprint('api_v1', __name__, url_prefix='/v1')


@api.route('/', methods=['GET'])
def root():
    run_on_kubernetes = True if environ.get("KUBERNETES_SERVICE_HOST") is not None else False
    return jsonify({
        "version": "0.1.0",
        "date": int(time.time()),
        "kubernetes": run_on_kubernetes
    })

@api.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "OK",
    })

@api_v1.route('/tools/lookup', methods=['GET'])
def lookup():
    domain = request.args.get('domain')
    return jsonify({
        "IP": socket.gethostbyname(domain)
    })

app.register_blueprint(get_swaggerui_blueprint(
    '/api/docs',
    '/static/swagger.json',
    config={ 
        'app_name': "Documentation"
    },
))
app.register_blueprint(api)
app.register_blueprint(api_v1)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
