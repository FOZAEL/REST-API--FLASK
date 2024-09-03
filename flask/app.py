from flask import Flask, Blueprint, jsonify, request
import time
import socket
from os import environ
from flask_swagger_ui import get_swaggerui_blueprint
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DomainLookup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_time = db.Column(db.Integer, nullable=False)
    client_ip = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    query_status = db.Column(db.String(10), nullable=False)
    response_time = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<DomainLookup {self.domain} - {self.ip_address}>"
    
with app.app_context():
    db.create_all()

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

def is_valid_domain(domain):
    pattern = re.compile(
        r'^(?=.{1,253}$)(?=.{1,63}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?!-)[A-Za-z0-9-]{1,63}(?<!-)$'
    )
    return pattern.match(domain) is not None

def dns_lookup(domain):
    try:
        start_time = time.time()
        
        result = socket.getaddrinfo(domain, None, socket.AF_INET)
        ip_addresses = [item[4][0] for item in result]
        
        response_time = time.time() - start_time
        return ip_addresses, response_time
    except socket.gaierror:
        return [], None

@api_v1.route('/tools/lookup', methods=['GET'])
def lookup():
    domain = request.args.get('domain')
    if not is_valid_domain(domain):
        return jsonify({"message": "Domain parameter is Not Valid or Provided"}), 400
    
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    query_id = int(time.time() * 1000)
    created_time = int(time.time())

    ip_addresses, response_time = dns_lookup(domain)
    addresses = []

    query_status = 'success' if ip_addresses else 'failure'

    if query_status == 'failure':
        return jsonify({"message": "The Host IP Not Found"}), 404

    for ip in ip_addresses:
        addresses.append({"ip": ip, "queryID": query_id})
        
        lookup_record = DomainLookup(
            domain=domain,
            ip_address=ip,
            created_time=created_time,
            client_ip=client_ip,
            user_agent=user_agent,
            query_status=query_status,
            response_time=response_time
        )
        db.session.add(lookup_record)

    db.session.commit()

    response = {
        "addresses": addresses,
        "client_ip": client_ip,
        "created_time": created_time,
        "domain": domain,
        "queryID": query_id
    }
    app.logger.info(response)
    return jsonify(response)

@api_v1.route('/tools/validate', methods=['POST'])
def validate():
    data = request.get_json()
    pattern = re.compile(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    responce = {"ip" : "is a Valid ipV4"} if pattern.match(data.get('ip')) is not None else {"ip" : "is NOT a Valid ipV4"}
    app.logger.info(responce)
    return jsonify(responce)
    

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
