from flask import Flask, url_for, session, request, jsonify, redirect
from flask_oauthlib.client import OAuth

CLIENT_ID = 'SjHWna6K40tQdqyVAxEDjR5EGpbLM741oOWJRSz0'
CLIENT_SECRET = 'n7T1j51NOFn3ARfrsFOnCrblDUBnPz2yIKcQ5VhSMye3W1YK01'

app = Flask(__name__)
app.debug = True
app.secret_key = 'secret'
oauth = OAuth(app)

remote = oauth.remote_app(
    'remote',
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
    request_token_params={'scope': 'email'},
    base_url='http://127.0.0.1:5000/',
    request_token_url=None,
    access_token_url='http://127.0.0.1:5000/oauth/token',
    authorize_url='http://127.0.0.1:5000/oauth/authorize'
)


@app.route('/logout')
def logout():
    if 'remote_oauth' in session:
        remote.get('logout')
        session.pop('remote_oauth', None)
    return redirect('/')


@app.route('/')
def index():
    if 'remote_oauth' in session:
        resp = remote.get('/me')
        if resp.status == 401:
            session.pop('remote_oauth', None)
            return redirect('/')
        return 'Ready! ' + resp.data['username'] + '\nToken: ' + session['remote_oauth'][0]
    next_url = request.args.get('next') or request.referrer or None
    callback = url_for('authorized', next=next_url, _external=True)
    return remote.authorize(callback)


@app.route('/authorized')
def authorized():
    resp = remote.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if 'access_token' in resp.keys():
        session['remote_oauth'] = (resp['access_token'], '')
    # return jsonify(oauth_token=resp['access_token'])
    return redirect('/')


@remote.tokengetter
def get_oauth_token():
    return session.get('remote_oauth')


# Utils
##################################################

@app.route('/createUser')
def createUser():
    data = {'email': 'basi@hot.com', 'pass': 'test', 'carts': [{'name': 'mama', 'items': []}]}
    resp = remote.post('clients', data, format='json')
    if resp.status == 201:
        return jsonify(resp.data)
    else:
        return str(resp.status)


@app.route('/addCart')
def addCart():
    data = {'name': 'papa', 'items': []}
    resp = remote.post('/clients/basi@hot.com', data, format='json')
    if resp.status == 201:
        return jsonify(resp.data)
    else:
        return str(resp.status)


@app.route('/clients')
def printClients():
    resp = remote.get('/clients')
    if resp.status == 200:
        return jsonify(resp.data)
    else:
        return str(resp.status)


if __name__ == '__main__':
    import os
    os.environ['DEBUG'] = 'true'
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    app.run(host='localhost', port=8000)
