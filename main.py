#
# This is a minimal server-side web application that authenticates visitors
# using Google Sign-in.
# 
# See the README.md and LICENSE.md files for the purpose of this code.
#

# ENVIRONMENT VARIABLES YOU MUST SET
#
# The following values must be provided in environment variables for Google
# Sign-in to work.
#
# These must be registered with, or provided by, the Google Cloud project:
# CLIENT_ID = 'Fill this in'
# CLIENT_SECRET = 'Fill this in'
# REDIRECT_URI = 'Fill this in'
#
# This must be set to a chosen (preferably randomly) value
# SESSION_SECRET = 'Fill this in'


from flask import Flask, redirect, render_template, request, session

import logging
import os
import requests

# Authentication helper libraries
from google.oauth2 import id_token
from google.auth.transport import requests as reqs

app = Flask(__name__)
app.secret_key = os.environ['SESSION_SECRET'].encode()  # Must be bytes


@app.route('/')
def homepage():
    # If user has signed in (has a valid session), welcome them. Otherwise,
    # direct them to page to start that sign-in and get a valid session.
    if 'email' not in session:
        return redirect('/unauthenticated')
    return render_template('index.html', email=session['email'])


@app.route('/unauthenticated')
def unauthenticated():
    # Show a page with a link for the user to sign in with. The link is to a
    # Google sign-in page, and must have the form shown
    url = 'https://accounts.google.com/signin/oauth?response_type=code&'
    url += 'client_id={}&'.format(os.environ['CLIENT_ID'])
    url += 'scope=openid%20email&'
    url += 'redirect_uri={}&'.format(os.environ['REDIRECT_URI'])
    url += 'state={}&'.format('/')  # After sign-in, redirect user to root URL

    return render_template('unauthenticated.html', sign_in_url=url)


@app.route('/privacy')
def privacy_policy():
    # Display the privacy policy.
    return render_template('privacy.html')


@app.route('/callback')
def callback():
    # If the user successfully signs in with Google, their browser will be
    # redirected to this page. The redirect URL includes query parameters
    # that can be used to get the user's identity.
    args = request.args.to_dict()
    redirect_path = args['state']
    code = args['code']

    # Ask a Google service to provide the user information associated with
    # the code that provided in the redirect URL's query parameter.
    resp = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': os.environ['CLIENT_ID'],
        'client_secret': os.environ['CLIENT_SECRET'],
        'redirect_uri': os.environ['REDIRECT_URI'],
        'grant_type': 'authorization_code'
    })

    # Retrieve the id_token field from the JSON response.
    token = resp.json()['id_token']

    # Verify the token's validity (such as proper signature from Google) and
    # extract the email address from it, if possible.
    try:
        info = id_token.verify_oauth2_token(token, reqs.Request())
        if 'email' not in info:
            return render_template('error.html'), 403
        session['email'] = info['email']
    except Exception as e:
        logging.warning('Request has bad OAuth2 id token: {}'.format(e))
        return render_template('error.html'), 403

    # Response will include the session token that now include the email.
    return redirect('/')


# The following is used for local or other non-App Engine deployment
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)