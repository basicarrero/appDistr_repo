#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-
u"""
oauth wrapper
"""
from flask import Flask, jsonify, abort, make_response, request, \
                  render_template, session
from datetime import datetime, timedelta
from flask_oauthlib.provider import OAuth2Provider
from werkzeug.security import gen_salt
from vinos_core import db, getUser, getUserbyName, User

app = Flask(__name__, template_folder='templates')
app.debug = True
app.secret_key = 'secret'
app.config.update({'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite', })
oauth = OAuth2Provider(app)


class Client(db.Model):
    global db
    user_id = db.Column(db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User')

    client_id = db.Column(db.String(40))
    client_secret = db.Column(db.String(55), nullable=False)

    _redirect_uris = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')
    )
    user = db.relationship('User')

    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id')
    )
    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


@oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user(),
        expires=expires
    )
    db.session.add(grant)
    db.session.commit()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.query.filter_by(
        client_id=request.client.client_id,
        user_id=request.user.id
    )
    # make sure that every client has only one token connected to a user
    for t in toks:
        db.session.delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    db.session.add(tok)
    db.session.commit()
    return tok


@app.route('/oauth/token', methods=['GET', 'POST'])
@oauth.token_handler
def access_token():
    return None


@app.route('/oauth/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        # print kwargs
        return render_template('logIn.html', **kwargs)
    else:
        username = request.form.get('username')
        passwd = request.form.get('passwd')
        user = getUserbyName(username)
        if user and user.passwd == passwd:
            session['id'] = user.id
            return True
        return False


def setClient(user):
    try:
        print 'Access Granted! --> User_Id: ',
        print str(user.id), 'User_Name: ' + user.username
        client = Client(
            client_id=gen_salt(40),
            client_secret=gen_salt(50),
            _redirect_uris='http://127.0.0.1:8000/authorized',
            _default_scopes='email',
            user_id=user.id,
        )
        db.session.add(client)
        db.session.commit()
        return client
    except Exception as e:
        print e
        abort(400)


def validateUsers(userList):
    user = request.oauth.user
    for u in userList:
        if u.upper() == user.username.upper():
            return user
    abort(401)


def current_user():
    if 'id' in session:
        uid = session['id']
        return getUser(uid)
    return None


# RESOURCES:
#############################################################################

@app.route('/clients',
           methods=['GET', 'POST'])
@oauth.require_oauth()
def oauth_manager_clients():
    validateUsers(['root'])
    from vinos_core import manager_clients
    response = manager_clients()
    if response.status_code == 201:
        username = request.json.get('email', "")
        setClient(getUserbyName(username))
    return response


@app.route('/clients/<id_cli>',
           methods=['GET', 'POST', 'PUT', 'DELETE'])
@oauth.require_oauth()
def oauth_manager_client(id_cli):
    validateUsers(['root', id_cli])
    from vinos_core import manager_client
    return manager_client(id_cli)


@app.route('/clients/<id_cli>/carts/<id_cart>',
           methods=['GET', 'PUT', 'DELETE'])
@oauth.require_oauth()
def oauth_manager_cart(id_cli, id_cart):
    validateUsers(['root', id_cli])
    from vinos_core import manager_cart
    return manager_cart(id_cli, id_cart)


@app.route('/clients/<id_cli>/carts/<id_cart>/item/<id_it>',
           methods=['PUT', 'DELETE'])
@oauth.require_oauth()
def oauth_manager_cartItems(id_cli, id_cart, id_it):
    validateUsers(['root', id_cli])
    from vinos_core import manager_cartItems
    return manager_cartItems(id_cli, id_cart, id_it)


@app.route('/wines', methods=['GET'])
def oauth_get_wines():
    from vinos_core import get_wines
    return get_wines()


@app.route('/wines', methods=['POST', 'DELETE'])
@oauth.require_oauth()
def oauth_manager_wines():
    validateUsers(['root'])
    from vinos_core import manager_wines
    return manager_wines()


@app.route('/wines/<id_wine>', methods=['GET'])
def oauth_get_wine(id_wine):
    from vinos_core import get_wine
    return get_wine(id_wine)


@app.route('/wines/<id_wine>', methods=['PUT', 'DELETE'])
@oauth.require_oauth()
def oauth_manager_wine(id_wine):
    validateUsers(['root'])
    from vinos_core import manager_wine
    return manager_wine(id_wine)


@app.route('/wines/byType/<typeStr>', methods=['GET'])
def oauth_manager_wineType(typeStr):
    from vinos_core import manager_wineType
    return manager_wineType(typeStr)


@app.route('/logout', methods=['GET'])
@oauth.require_oauth()
def logOut():
    user = request.oauth.user
    session.pop('id', None)
    return make_response(jsonify({"LogedOut": user.username}), 200)


@app.route('/me')
@oauth.require_oauth()
def me():
    return jsonify(username=request.oauth.user.username)


if __name__ == '__main__':
    db.create_all()
    # Got root?
    if not getUserbyName('root'):
        root = User(username='root', passwd='root', id=1)
        client = Client(
            client_id='SjHWna6K40tQdqyVAxEDjR5EGpbLM741oOWJRSz0',
            client_secret='n7T1j51NOFn3ARfrsFOnCrblDUBnPz2yIKcQ5VhSMye3W1YK01',
            _redirect_uris='http://127.0.0.1:8000/authorized',
            _default_scopes='email',
            user_id=1,
        )
        db.session.add(root)
        db.session.add(client)
        db.session.commit()
    app.run(debug=True)
