#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-
u"""
vinos core server
"""
from flask import Flask, jsonify, abort, make_response, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import gen_salt
import base64


app = Flask(__name__, template_folder='templates')
app.debug = True
app.secret_key = 'secret'
app.config.update({'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite', })
db = SQLAlchemy(app)
L_SALT = 3


class Wine(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    grade = db.Column(db.Integer)
    size = db.Column(db.Integer)
    do = db.Column(db.Boolean)
    varietals = db.Column(db.PickleType)
    photo = db.Column(db.String(150))
    name = db.Column(db.String(40))
    price = db.Column(db.Float)
    cask = db.Column(db.Integer)
    bottle = db.Column(db.Integer)

    def update(self, request):
        self.grade = request.json.get('grade', 12)
        self.size = request.json.get('size', 75)
        self.varietals = request.json.get('varietals', [])
        self.do = request.json.get('do', False)
        self.price = request.json.get('price', None)
        self.name = request.json['name']
        self.photo = request.json.get('photo', None)
        self.cask = request.json.get('cask', None)
        self.bottle = request.json.get('bottle', None)
        db.session.commit()

    def toDict(self):
        new = {
               'id': self.id,
               'name': self.name,
               'price': self.price,
               'grade': self.grade,
               'size': self.size,
               'do': self.do,
               'varietals': self.varietals,
               'photo': self.photo,
               }
        if self.cask:
            new['cask'] = self.cask
        if self.bottle:
            new['bottle'] = self.bottle
        return new


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    passwd = db.Column(db.String(40))
    address = db.Column(db.String(40))
    phone = db.Column(db.String(15))
    carts = db.Column(db.PickleType)

    def addCart(self, requests, id_cart="cart_" + gen_salt(L_SALT)):
        if not request.json and 'items' not in request.json:
            abort(400)
        return self.addCartParam(id_cart,
                                 request.json.get('name', ""),
                                 request.json.get('items', []))

    def addCartParam(self, id_cart, name, items=[]):
        for i in items:
            if not Wine.query.filter_by(id=unicode(i)).first():
                abort(404)
        lst = [{'id': id_cart, 'name': name, 'items': items}]
        lst.extend(self.carts)
        self.carts = lst
        db.session.commit()
        return lst[0]

    def getCart(self, cart_id):
        for c in self.carts:
            if c['id'] == cart_id:
                return c
        return None

    def addItem(self, cart_id, item_id):
        if not Wine.query.filter_by(id=unicode(item_id)).first():
            abort(404)
        cartList = []
        for c in self.carts:
            if c['id'] == cart_id:
                new_items = [item_id]
                new_items.extend(c['items'])
                c = {'id': cart_id,
                     'name': c['name'],
                     'items': new_items
                     }
            cartList.append(c)
        self.carts = cartList
        db.session.commit()
        return self.carts

    def delItem(self, cart_id, item_id):
        cartList = []
        for c in self.carts:
            if c['id'] == cart_id:
                c = {'id': cart_id,
                     'name': c['name'],
                     'items': [i for i in c['items'] if i != item_id]
                     }
            cartList.append(c)
        self.carts = cartList
        db.session.commit()
        return self.carts

    def updateCart(self, cart_id, request):
        items = request.json.get('items', [])
        for i in items:
            if not Wine.query.filter_by(id=unicode(i)).first():
                abort(404)
        cartList = []
        for c in self.carts:
            if c['id'] == cart_id:
                c = {'id': cart_id,
                     'name': request.json.get('name', ""),
                     'items': items
                     }
            cartList.append(c)
        self.carts = cartList
        db.session.commit()
        return self.carts

    def removeCart(self, cart):
        self.carts = [c for c in self.carts if c != cart]
        db.session.commit()
        return self.carts

    def update(self, request):
        self.username = request.json.get('email', "")
        self.passwd = request.json.get('pass', "")
        self.address = request.json.get('address', None)
        self.phone = request.json.get('phone', None)
        self.carts = request.json.get('carts', [])
        db.session.commit()

    def toDict(self):
        return {
               'email': self.username,
               'pass': self.passwd,
               'carts': self.carts,
               'address': self.address,
               'phone': self.phone
               }


@app.route('/', methods=['GET'])
def hello():
    return make_response(__doc__, 200)


def addUser(request):
    if not request.json or 'email' not in request.json \
                            or 'pass' not in request.json:
            abort(400)
    try:
        cartList = request.json.get('carts', [])
        for c in cartList:
            c['id'] = "cart_" + gen_salt(L_SALT)
        user = User(username=request.json.get('email', ""),
                    passwd=request.json.get('pass', ""),
                    address=request.json.get('address', None),
                    phone=request.json.get('phone', None),
                    carts=cartList)
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print e
        abort(400)
    return user


def addWine(request):
    if not request.json or 'name' not in request.json:
            abort(400)
    idWine = base64.b64encode(request.json['name'] + gen_salt(L_SALT))
    try:
        wine = Wine(id=idWine,
                    grade=request.json.get('grade', 12),
                    size=request.json.get('size', 75),
                    varietals=request.json.get('varietals', []),
                    do=request.json.get('do', False),
                    price=request.json.get('price', None),
                    name=request.json['name'],
                    photo=request.json.get('photo', None),
                    cask=request.json.get('cask', None),
                    bottle=request.json.get('bottle', None))
        db.session.add(wine)
        db.session.commit()
    except Exception as e:
        print e
        abort(400)
    return wine


def delUser(user):
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        print e
        abort(400)


def delWine(wine):
    try:
        db.session.delete(wine)
        db.session.commit()
    except Exception as e:
        print e
        abort(400)


def getUserbyName(username):
    return User.query.filter_by(username=username).first()


def getUser(uid):
    return User.query.get(uid)


def getWine(wine_id):
    return Wine.query.get(wine_id)


@app.route('/clients', methods=['GET', 'POST'])
def manager_clients():
    if request.method == 'POST':
        user = addUser(request)
        return make_response(jsonify({"created": user.username}), 201)
    elif request.method == 'GET':
        userList = [u.toDict() for u in User.query.all() if u.username != 'root']
        return make_response(jsonify({"clients": userList}), 200)


@app.route('/clients/<id_cli>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manager_client(id_cli):
    user = getUserbyName(id_cli)
    update = False
    if user:
        update = True
        if request.method == 'GET':
            return make_response(jsonify(user.toDict()), 200)
        elif request.method == 'POST':
            new_cart = user.addCart(request)
            return make_response(jsonify({"created": new_cart}), 201)
        elif request.method == 'DELETE':
            delUser(user)
            return make_response(jsonify({"removed": user.toDict()}), 200)

    if request.method == 'PUT':
        if update:
            user.update(request)
            return make_response(jsonify({"updated": user.toDict()}), 200)
        else:
            user = addUser(request)
            return make_response(jsonify({"created": user.toDict()}), 201)
    abort(404)


@app.route('/clients/<id_cli>/carts/<id_cart>', methods=['GET', 'PUT', 'DELETE'])
def manager_cart(id_cli, id_cart):
    user = getUserbyName(id_cli)
    if user:
        cart = user.getCart(id_cart)
        update = False
        if cart:
            update = True
            if request.method == 'GET':
                return make_response(jsonify({"items": cart['items']}), 200)
            elif request.method == 'DELETE':
                user.removeCart(cart)
                return make_response(jsonify({"removed": cart}), 200)

        if request.method == 'PUT':
            if update:
                new_cart = user.updateCart(id_cart, request)
                return make_response(jsonify({"updated": new_cart}), 200)
            else:
                new_cart = user.addCart(request, id_cart=id_cart)
                return make_response(jsonify({"created": new_cart}), 201)
    abort(404)


@app.route('/clients/<id_cli>/carts/<id_cart>/item/<id_it>', methods=['PUT', 'DELETE'])
def manager_cartItems(id_cli, id_cart, id_it):
    user = getUserbyName(id_cli)
    if user:
        cart = user.getCart(id_cart)
        if request.method == 'PUT':
            if cart:
                new_cart = user.addItem(cart['id'], id_it)
                return make_response(jsonify({"updated": new_cart}), 200)
            else:
                new_cart = user.addCartParam(id_cart, request.json.get('name', ""), [id_it])
                return make_response(jsonify({"created": new_cart}), 201)
        elif request.method == 'DELETE':
            if cart and id_it in cart['items']:
                user.delItem(cart['id'], id_it)
                return make_response(jsonify({"removed": id_it}), 200)
    abort(404)


@app.route('/wines', methods=['GET'])
def get_wines():
    id_wines = [w.toDict() for w in Wine.query.all()]
    return make_response(jsonify({"wines": id_wines}), 200)


@app.route('/wines', methods=['POST', 'DELETE'])
def manager_wines():
    if request.method == 'POST':
        wine = addWine(request)
        return make_response(jsonify({"created": wine.id}), 201)
    elif request.method == 'DELETE':
        db.session.query(Wine).delete()
        db.session.commit()
        return make_response("all wines deleted", 200)
    abort(404)


@app.route('/wines/<id_wine>', methods=['GET'])
def get_wine(id_wine):
    wine = getWine(id_wine)
    if wine:
        return make_response(jsonify(wine.toDict()), 200)
    else:
        abort(404)


@app.route('/wines/<id_wine>', methods=['PUT', 'DELETE'])
def manager_wine(id_wine):
    if request.method == 'DELETE':
        wine = getWine(id_wine)
        if wine:
            delWine(wine)
            return make_response(jsonify({"removed": wine.toDict()}), 200)
        else:
            abort(404)
    elif request.method == 'PUT':
        wine = getWine(id_wine)
        if wine:
            wine.update(request)
            return make_response(jsonify({"updated": wine.toDict()}), 200)
        else:
            newWine = addWine(request)
            return make_response(jsonify({"created": newWine.id}), 201)
    abort(404)


@app.route('/wines/byType/<typeStr>', methods=['GET'])
def manager_wineType(typeStr):
    if typeStr == 'tinto':
        tintos = Wine.query.filter(db.or_(Wine.cask != None, Wine.bottle != None)).all()
        return make_response(jsonify({"red": [w.name for w in tintos]}), 200)
    elif typeStr == 'blanco':
        blancos = Wine.query.filter(Wine.cask == None).filter(Wine.bottle == None).all()
        return make_response(jsonify({"white": [w.name for w in blancos]}), 200)
    else:
        abort(404)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
