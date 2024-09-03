from flask import Flask, Blueprint, jsonify, request
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

def dns_lookup(domain):
    try:
        result = socket.getaddrinfo(domain, None, socket.AF_INET)
        ip_addresses = [item[4][0] for item in result]
        return ip_addresses
    except socket.gaierror:
        return []


@api_v1.route('/tools/lookup', methods=['GET'])
def lookup():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"message": "Domain parameter is required"}), 400  
    client_ip = request.remote_addr
    query_id = int(time.time() * 1000)
    created_time = int(time.time())

    ip_addresses = dns_lookup(domain)
    addresses = [{"ip": ip, "queryID": query_id} for ip in ip_addresses]

    response = {
        "addresses": addresses,
        "client_ip": client_ip,
        "created_time": created_time,
        "domain": domain,
        "queryID": query_id
    }

    return jsonify(response)

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
