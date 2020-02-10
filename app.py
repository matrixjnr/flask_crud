from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'vehicles.db')
app.config['JWT_SECRET_KEY'] = 'not-a-secret'
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('DB Created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('DB Dropped!')


@app.cli.command('db_seed')
def db_seed():
    vehicle1 = Vehicles(vname='Romeo Pourche', vtype='Sports Car', vowner='Poursche', vd='1003.87')
    vehicle2 = Vehicles(vname='E Class', vtype='Jeep', vowner='Mercedes Benz', vd='1058.0')
    vehicle3 = Vehicles(vname='Prado', vtype='Land Rover', vowner='Toyota', vd='54.9')

    db.session.add(vehicle1)
    db.session.add(vehicle2)
    db.session.add(vehicle3)

    test_user = User(first_name='John', last_name='Matrix', email='jmatrix@mia.com', password='567890qw')

    db.session.add(test_user)
    db.session.commit()
    print('DB Seeded!')


@app.route('/')
def index():
    return jsonify(message='Welcome to Flask Rest API'), 200

# crouting
@app.route('/hello')
def hello():
    return 'Hello World', 200


@app.route('/param')
def param():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message='sorry ' + name + ', you are not old enough'), 401
    else:
        return jsonify(message='welcome ' + name + ', you are old enough')


@app.route('/vars/<string:name>/<int:age>')
def var(name: str, age: int):
    if age < 18:
        return jsonify(message='sorry ' + name + ', you are not old enough'), 401
    else:
        return jsonify(message='welcome ' + name + ', you are old enough')


@app.route('/vehicles', methods=['GET'])
def vehicles():
    v_list = Vehicles.query.all()
    result = vehicles_schema.dump(v_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='Email already exists!'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)

        db.session.add(user)
        db.session.commit()
        return jsonify(message='User registered successfully!'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login SSuccessful!', access_token=access_token)
    else:
        return jsonify(message='Wrong credentials!'), 401


@app.route('/retrieve_pass/<string:email>', methods=['GET'])
def retrieve_pass(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Your Vehicles Collection password is ' + user.password, sender='support@vehicles.com', recipients=[email])
        mail.send(msg)
        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message='That email does not exist'), 401


@app.route('/vehicle/<int:id>', methods=['GET'])
def vehicle(id: int):
    vehicle = Vehicles.query.filter_by(vid=id).first()
    if vehicle:
        result = vehicle_schema.dump(vehicle)
        return jsonify(result)
    else:
        return jsonify(message='Vehicle does not exist'), 404


@app.route('/add_vehicle', methods=['POST'])
@jwt_required
def add_vehicle():
    vehicle_name = request.form['vname']
    test = Vehicles.query.filter_by(vname=vehicle_name).first()
    if test:
        return jsonify(message='That vehicle already exists!'), 409  # conflict
    else:
        vtype = request.form['vtype']
        vowner = request.form['vowner']
        vd = float(request.form['vd'])

        new_vehicle = Vehicles(vname=vehicle_name, vtype=vtype, vowner=vowner, vd=vd)
        db.session.add(new_vehicle)
        db.session.commit()
        return jsonify(message='New vehicle added to collection'), 201


@app.route('/update_vehicle', methods=['PUT'])
@jwt_required
def update_vehicle():
    vid = int(request.form['vid'])
    vehicle = Vehicles.query.filter_by(vid=vid).first()
    if vehicle:
        vehicle.vname = request.form['vname']
        vehicle.vtype = request.form['vtype']
        vehicle.vowner = request.form['vowner']
        vehicle.vd = float(request.form['vd'])
        db.session.commit()
        return jsonify(message='Vehicle updated successfully!'), 202
    else:
        return jsonify(message='That vehicle does not exist!'), 404


@app.route('/delete_vehicle/<int:vid>', methods=['DELETE'])
@jwt_required
def delete_vehicle(vid: int):
    vehicle = Vehicles.query.filter_by(vid=vid).first()
    if vehicle:
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify(message='Planet deleted!'), 202
    else:
        return jsonify(message='Planet does not exist!'), 404


#  db models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Vehicles(db.Model):
    __tablename__ = 'vehicles'
    vid = Column(Integer, primary_key=True)
    vname = Column(String)
    vtype = Column(String)
    vowner = Column(String)
    vd = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class VehiclesSchema(ma.Schema):
    class Meta:
        fields = ('vid', 'vname', 'vtype', 'vowner', 'vd')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

vehicle_schema = VehiclesSchema()
vehicles_schema = VehiclesSchema(many=True)


if __name__ == '__main__':
    app.run(port='4500')
