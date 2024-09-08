from flask import Flask, Blueprint, jsonify, request, Response
import time
import socket
from os import environ
from flask_swagger_ui import get_swaggerui_blueprint
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, generate_latest, Summary
import re

app = Flask(__name__)

# Prometheus Metrics
view_metric = Counter('view', 'lookup view', ['lookup'])
duration = Summary('duration_compute_seconds', 'Time spent in the lookup() function')
endpoint_call_counter = Counter('endpoint_calls', 'Number of calls to each endpoint', ['endpoint'])

@app.before_request
def track_endpoint_call():
    endpoint = f"{request.endpoint}"
    endpoint_call_counter.labels(endpoint=endpoint).inc()

# DB
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DomainLookup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    ip_addresses = db.Column(db.JSON, nullable=True)
    created_time = db.Column(db.Integer, nullable=False)
    client_ip = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    query_status = db.Column(db.String(10), nullable=False)
    response_time = db.Column(db.Float, nullable=True)
    query_id = db.Column(db.String(45), nullable=False)

    def __repr__(self):
        return f"<DomainLookup {self.domain} - {self.ip_address}>"
    
with app.app_context():
    db.create_all()

api = Blueprint('api', __name__, url_prefix='/')
api_v1 = Blueprint('api_v1', __name__, url_prefix='/v1')


@api.route('/', methods=['GET'])
def root():
    run_on_kubernetes = True if environ.get("KUBERNETES_SERVICE_HOST") is not None else False
    response = {
        "version": "0.1.0",
        "date": int(time.time()),
        "kubernetes": run_on_kubernetes
    }
    app.logger.info(response)
    return jsonify(response)

@api.route('/health', methods=['GET'])
def health():
    response = {
        "status": "OK",
    }
    app.logger.info(response)
    return jsonify(response)

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
@duration.time()
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
        if not any(address['ip'] == ip for address in addresses):
            addresses.append({"ip": ip, "queryID": query_id})
        
    lookup_record = DomainLookup(
        domain=domain,
        ip_addresses=addresses,
        created_time=created_time,
        client_ip=client_ip,
        user_agent=user_agent,
        query_status=query_status,
        response_time=response_time,
        query_id=query_id
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
    view_metric.labels(lookup=domain).inc()
    app.logger.info(response)
    return jsonify(response)

@api_v1.route('/tools/validate', methods=['POST'])
def validate():
    data = request.get_json()
    pattern = re.compile(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )
    response = {"ip" : "is a Valid ipV4"} if pattern.match(data.get('ip')) is not None else {"ip" : "is NOT a Valid ipV4"}
    app.logger.info(response)
    return jsonify(response)

@api_v1.route('/history', methods=['GET'])
def history():
    last_queries = DomainLookup.query.order_by(DomainLookup.created_time.desc()).limit(20).all()
    if ( last_queries is None ):
        return jsonify({"message": "Database is empty, do some query first"}), 400
    response = []
    for query in last_queries:
        response.append({
            "addresses": query.ip_addresses,
            "client_ip": query.client_ip,
            "created_time": query.created_time,
            "domain": query.domain,
            "queryID": query.query_id
        })

    app.logger.info(response)
    return jsonify(response)


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

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
