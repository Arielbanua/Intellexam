from flask import Flask, render_template, flash, request, redirect, url_for
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user



app = Flask(__name__)

#add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#secret key
app.config['SECRET_KEY'] = "secret"

#initalize database
db = SQLAlchemy(app)

#flask login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#create model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique =True)
    password = db.Column(db.String(128))


    #create a string
    def __repr__(self):
        return '<Name %r>' % self.name
    
# Create database within app context
with app.app_context():
    db.create_all()


# create registration form
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(),])
    submit = SubmitField("Submit")

# create login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(),])
    submit = SubmitField("Submit")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Users(name=form.name.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            form.name.data = ''
            form.password.data = ''
            form.email.data = ''
            flash("User Added Successfully!")
            return redirect(url_for('login'))

        else:
            form.name.data = ''
            form.password.data = ''
            form.email.data = ''
            flash("Email taken!")
    return render_template("register.html", form=form) 

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(email=form.email.data).first()
		if user:
			# Check the hash
			if (user.password == form.password.data):
				login_user(user)
				flash("Login Succesfull!!")
				return redirect(url_for('home'))
			else:
				flash("Wrong Password - Try Again!")
		else:
			flash("That User Doesn't Exist! Try Again...")

	return render_template('login.html', form=form)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if(request.form['answer'] == ''):
            return "<html><body> <h1>Invalid answer</h1></body></html>"
        else:
            answer = request.form['answer']
            print('test')
            sentences = ["this is a very good sentence", answer]

            model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            embeddings = model.encode(sentences)
            result = cosine_similarity([embeddings[0]], embeddings[1:])

            return render_template('answer.html', answer=answer, result=result)
    if request.method == 'GET':
        return render_template("index.html")

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)