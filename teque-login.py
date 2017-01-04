from flask import Flask, session, url_for, request
from flask_oauth import OAuth
from flask_oauthlib.provider import OAauth2Provider
import pickle, json
import config

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY
oauth = OAuth()
oauth_prov = OAauth2Provider()

FACEBOOK_APP_ID = config.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET = config.FACEBOOK_APP_SECRET
FACEBOOK_GROUP_ID = config.FACEBOOK_GROUP_ID

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
	consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/oauth")
def auth():
	print "stuff is happening"
	return facebook.authorize(callback=url_for('check_auth', next=request.args.get('next') or request.referrer or None, _external=True))

def is_in_group(facebook, id):
	try:
		with open('members.cfg','rb') as f:
			id_list = pickle.load(f)
			if id in id_list:
				return True
	except:
		pass
	members = facebook.get(FACEBOOK_GROUP_ID+'/members?limit=5000').data['data'] #is it bad practice to assume members<5000? yes. Is it sufficient? yes.
	#print repr(members)
	id_list = [member['id'] for member in members]
	if id in id_list:
		with open('members.cfg','wb+') as f:
			pickle.dump(id_list, f)
			return True
	return False
	

def user_handler(facebook, me):
	strb = 'Logged in as id=%s name=%s redirect=%s' % (me.data['id'], me.data['name'], request.args.get('next'))
	if is_in_group(facebook, me.data['id']):
		strb+="<br/>MEMBER</br>"
	return strb

@app.route("/authorized")
@facebook.authorized_handler
def check_auth(response):
	if response is None:
		return 'Access denied: reason=%s error=%s' % (
			request.args['error_reason'],
			request.args['error_description']
		)
	session['oauth_token'] = (response['access_token'], '')
	me = facebook.get('/me')
	return user_handler(facebook, me)
		
@facebook.tokengetter
def get_facebook_oauth_token():
	return session.get('oauth_token')
	
if __name__ == "__main__":
	oauth_prov.init(app)
    app.run()
