######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

from calendar import c
import pickletools
from re import A
# from winreg import DeleteValue
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
from datetime import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

class Anonymous(flask_login.mixins.AnonymousUserMixin):
  def __init__(self):
    self.id = -1

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()


def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

def getUserListById():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			user_id = getUserIdFromEmail(email)
			return flask.redirect(flask.url_for('protected', uid = user_id)) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	# return render_template('hello.html', message='Logged out')
	return flask.redirect(flask.url_for('hello'))

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', suppress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		dob = request.form.get('dob')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, dob) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, password, first_name, last_name, dob)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		user_id = getUserIdFromEmail(email)
		return flask.redirect(flask.url_for('protected', uid = user_id))
	else:
		print("email is already used")
		return flask.redirect(flask.url_for('register'))

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserNameFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()

def getUserNameFromId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile/<uid>', methods=['GET'])
@flask_login.login_required
def protected(uid = -1):
	assert uid != -1
	if int(uid) != getUserIdFromEmail(flask_login.current_user.id):
		userList = getUserListById()
		if uid not in str(userList):
			return flask.redirect(flask.url_for('protected', uid=getUserIdFromEmail(flask_login.current_user.id)))
		name = getUserNameFromId(uid)
		return render_template('altProfile.html', name=" ".join(name))
	name = getUserNameFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=" ".join(name), message="Here's your profile")

#begin code for albums and photos management
# photos uploaded using base64 encoding so they can be directly embeded in HTML

def isPhotoOfCurrentUser(uid, pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
	picture_uid = cursor.fetchone()[0]
	return picture_uid == uid

def isAlbumOfCurrentUser(uid, aid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Albums WHERE album_id = '{0}'".format(aid))
	album_uid = cursor.fetchone()[0]
	return album_uid == uid

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id FROM Pictures")
	return cursor.fetchall() 

def getAllAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT album_id, name, date_created, first_name, last_name FROM Albums INNER JOIN Users ON Albums.user_id = Users.user_id")
	return cursor.fetchall()


def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name, date_created FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def deleteAlbum(aid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(aid))
	conn.commit()

def deletePicture(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
	aid = cursor.fetchone()[0]
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
	conn.commit()
	return aid

def getPicture(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, caption, picture_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()


def getAlbumsPhotos(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id FROM Pictures WHERE album_id = '{0}'".format(aid))
	return cursor.fetchall()

def getAlbumsName(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE album_id = '{0}'".format(aid))
	return cursor.fetchone()[0]

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/albums/<album_id>/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_photo(album_id = -1):
	assert album_id != -1
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s)''', (photo_data, uid, caption,album_id))
		conn.commit()
		return render_template('singleAlbumView.html', message='Photo uploaded!', photos=getAlbumsPhotos(album_id), base64=base64,name=getAlbumsName(album_id),aid=album_id)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html',aid=album_id)

# create album
@app.route('/albums/create', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		name = request.form.get('name')
		date_created = datetime.today().strftime('%Y-%m-%d')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (name, user_id, date_created) VALUES (%s, %s, %s )''', (name, uid, date_created))
		conn.commit()
		return render_template('albumsView.html', message='Album created!', albums=getUsersAlbums(uid))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('albumCreate.html')


@app.route("/photo/<pid>", methods=['GET'])
def get_single_photo(pid=-1):
	assert pid != -1
	if request.method == 'GET':
		if flask_login.current_user.id == -1 or not isPhotoOfCurrentUser(getUserIdFromEmail(flask_login.current_user.id), pid):
			return render_template('singlePhotoView.html', photo=getPicture(pid),base64=base64)
		else:
			return render_template('singlePhotoView.html', photo=getPicture(pid),base64=base64,canDelete="true")

	else:
		aid = deletePicture(pid)
		return redirect(url_for('get_single_album', album_id=aid),code=303)


@app.route("/photo/<pid>", methods=['DELETE'])
@flask_login.login_required
def delete_photo(pid=-1):
	assert pid != -1
	aid = deletePicture(pid)
	return redirect(url_for('get_single_album', album_id=aid),code=303)


@app.route('/albums/<album_id>', methods=['GET'])
def get_single_album(album_id=-1):
	assert album_id != -1
	if flask_login.current_user.id == -1 or not isAlbumOfCurrentUser(getUserIdFromEmail(flask_login.current_user.id), album_id):
		return render_template('singleAlbumView.html', photos=getAlbumsPhotos(album_id), name=getAlbumsName(album_id),aid=album_id,base64=base64)
	return render_template('singleAlbumView.html', photos=getAlbumsPhotos(album_id), name=getAlbumsName(album_id),aid=album_id,base64=base64,canDelete="true")

# delete album
@app.route('/albums/<album_id>', methods=['DELETE'])
@flask_login.login_required
def delete_album(album_id=-1):
	assert album_id != -1
	deleteAlbum(album_id)
	return redirect(url_for('get_all_user_albums'),code=303)

# albums view
@app.route("/albums", methods=['GET'])
@flask_login.login_required
def get_all_user_albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('albumsView.html', albums=getUsersAlbums(uid))

@app.route("/photos", methods=['GET'])
@flask_login.login_required
def get_all_user_photos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('photosView.html', photos=getUsersPhotos(uid),base64=base64)

@app.route("/all_albums", methods=['GET'])
def get_all_albums():
	return render_template('allAlbumsView.html', albums=getAllAlbums())

@app.route("/all_photos", methods=['GET'])
def get_all_photos():
	return render_template('allPhotosView.html', photos=getAllPhotos(),base64=base64)

#end code for albums and photos management

#begin code for friends management
def find_people(fname, lname):
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT user_id, first_name, last_name FROM Users WHERE user_id <> '{0}' AND (first_name = '{1}' OR last_name = '{2}')".format(uid, fname, lname))
	return cursor.fetchall()

def add_friend_(fid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Friendships (user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, fid))

def unfriend_(fid):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Friendships WHERE (Friendships.user_id = '{0}' AND Friendships.friend_id = '{1}') OR (Friendships.user_id = '{1}' AND Friendships.friend_id = '{0}')".format(uid, fid))
	conn.commit()

def get_all_friends_(uid):
	cursor = conn.cursor()
	cursor.execute("(SELECT Friendships.friend_id, Users.first_name, Users.last_name FROM Friendships INNER JOIN Users ON Friendships.friend_id = Users.user_id WHERE Friendships.user_id = '{0}') UNION (SELECT Friendships.user_id, Users.first_name, Users.last_name FROM Friendships INNER JOIN Users ON Friendships.user_id = Users.user_id WHERE Friendships.friend_id = '{0}')".format(uid))
	return cursor.fetchall()

@app.route("/friend_search", methods=['GET', 'POST'])
@flask_login.login_required
def friend_search():
	if flask.request.method == 'GET':
		return render_template('friendSearch.html')
	first_name = flask.request.form['first_name']
	last_name = flask.request.form['last_name']
	return render_template('friendSearch.html', people_list=find_people(first_name, last_name))

@app.route('/profile/<uid>', methods=['POST'])
@flask_login.login_required
def add_friend(uid=-1):
	assert uid != -1
	add_friend_(uid)
	return redirect(url_for('get_all_friends'))

@app.route('/profile/<uid>', methods=['DELETE'])
@flask_login.login_required
def unfriend(uid=-1):
	assert uid != -1
	unfriend_(uid)
	return redirect(url_for('get_all_friends'))

@app.route('/all_friends', methods=['GET'])
@flask_login.login_required
def get_all_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('friendsList.html', friends=get_all_friends_(uid))

#end code for friends management

#default page
@app.route("/", methods=['GET'])
def hello():
	if flask_login.current_user.is_authenticated:
		return flask.redirect(flask.url_for('protected', uid=getUserIdFromEmail(flask_login.current_user.id)))
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
	