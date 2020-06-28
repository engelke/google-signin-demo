#
# See the README.md and LICENSE.md files for the purpose of this code.
#

# GLOBAL VARIABLES YOU MUST SET
#
# These must be registered with, or provided by, the Google Cloud project:
CLIENT_ID = 'Fill this in'
CLIENT_SECRET = 'Fill this in'
REDIRECT_URL = 'Fill this in'


from flask import Flask, redirect, render_template, request, session

import logging
import requests
import uuid
from google.oauth2 import id_token
from google.auth.transport import requests as reqs

app = Flask(__name__)


@app.route('/')
def homepage():
    if 'email' not in session:
        return redirect('/unauthenticated')
    return render_template('index.html', email=email)


@app.route('/unauthenticated')
def unauthenticated():
    # Show a page with a link for the user to sign in with
    
    client_id = CLIENT_ID
    redirect_uri = REDIRECT_URI
    nonce = uuid.uuid4()

    url = 'https://accounts.google.com/signin/oauth?response_type=code&'
    url += 'client_id={}&'.format(client_id)
    url += 'scope=openid%20email&'
    url += 'redirect_uri={}&'.format(redirect_uri)
    url += 'state={}&'.format('/')  # After sign-in, redirect user to root URL
    url += 'nonce={}'.format(nonce)

    return render_template('unauthenticated.html', sign_in_url=url)


@app.route('/callback')
def callback():
    args = request.args.to_dict()
    redirect_path = args['state']
    code = args['code']

    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    redirect_uri = REDIRECT_URI

    resp = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    })

    id_token = resp.json()['id_token']
    email = None

    try:
        info = id_token.verify_oauth2_token(token, reqs.Request())
        if 'email' not in info:
            return render_template('error.html')
        session['email'] = info['email']
    except Exception as e:
        logging.warning('Request has bad OAuth2 id token: {}'.format(e))
        return render_template('error.html')

    return redirect('/')


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)