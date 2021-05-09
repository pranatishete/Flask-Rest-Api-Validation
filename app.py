from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from flask_marshmallow import Marshmallow
import requests
from marshmallow import Schema, fields, post_load, ValidationError, validates, validate
import time
import concurrent.futures
import threading
from flask import Flask, render_template


app = Flask(__name__, template_folder='templates')

app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stationery.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)

#API_HTTPBIN = 'https://httpbin.org/delay/{delay_value}'



class Stationery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(20))
    status = db.Column(db.String(20),default = "pending")

def validate_check(check: str):
  return check in ["book", "pen", "folder", "bag"]
 
class StationerySchema(ma.Schema):
    item = fields.String(required=True,
    validate = validate_check)



@app.route('/item',methods=['POST'])
def create_item():
    data = request.get_json()
    stat_schema = StationerySchema()
    try:
        result = stat_schema.load(data)
        print(result)
        new_item = Stationery( item = data['item'],status='pending')
        db.session.add(new_item)
        db.session.commit()
        query = Stationery.query.order_by(Stationery.id.desc()).first()
        return jsonify({'item': query.item,'status':query.status,"id":query.id})

    except ValidationError as err:

        return jsonify(err.messages,data), 400

    return jsonify(data), 200


@app.route('/display',methods=["GET"])
def display():
    if request.method == "GET":
        m = Stationery.query.all()
        return render_template("display.html", query=m)

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def trigger(url):
    session = get_session()
    with session.get(url) as response:
        print(f"Read {len(response.content)} from {url}")

thread_local = threading.local()

@app.route('/delay',methods=['GET'])
def concurrent_get():
    delay_value = request.args['value']
    start = time.perf_counter()
    endpoint = f"https://httpbin.org/delay/{delay_value}"
    li = [endpoint]*5
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(trigger, li) 
    print(list(results))
    total_time = time.time()-start
    return jsonify({"time_taken": total_time})

if __name__ == '__main__':
    app.run(debug=True)