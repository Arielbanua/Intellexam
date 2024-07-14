from flask import Flask, render_template, flash, request, redirect, url_for
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, DateTimeLocalField, TextAreaField, DateTimeField
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

class Tests(db.Model):
    test_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign Key To Link User (refer to primary key of the user)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # list of questions from the questions table
    questions = db.relationship("Questions", backref="test")
     
class Questions(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    question_type = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_opt = db.Column(db.Integer, nullable=False)
	# Foreign Key To Link test (refer to primary key of the test)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.test_id'))
    #one-to-one relationship with the Answer model
    answer = db.relationship("Answers", uselist=False)

class Answers(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(255), nullable=False)
    result = db.Column(db.Boolean, nullable=False) 
    chosen_opt = db.Column(db.Integer, nullable=False)
	# Foreign Key To Link to answer (refer to primary key of the question)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'))
    
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

# create create-test form
class TestForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    start_date = DateTimeLocalField('Start_date', validators=[DataRequired()])
    end_date = DateTimeLocalField("End_date", validators=[DataRequired()])
    submit = SubmitField("Submit")

class QuestionForm(FlaskForm):
    title = StringField("Email", validators=[DataRequired()])
    start_date = DateTimeField('Start_date', validators=[DataRequired()])
    end_date = DateTimeField("End__date", validators=[DataRequired()])

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

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))

@app.route('/create-test', methods=['GET', 'POST'])
def create_test():
    form = TestForm()
    if form.validate_on_submit():
        creator = current_user.id
        test = Tests(title=form.title.data, start_date=form.start_date.data, end_date=form.end_date.data, teacher_id=creator)
		# Clear The Form
        form.title.data = ''
        form.start_date.data = ''
        form.end_date.data = ''

		# Add test data to database
        db.session.add(test)
        db.session.commit()

		# Return a Message
        flash("Test Created Successfully!")
        return redirect(url_for('tests'))

	# Redirect to the webpage 
    return render_template("create_test.html", form=form)

@app.route('/tests', methods=['GET', 'POST'])
def tests():
     # Grab all the tests by the teacher from the database
	tests = Tests.query.filter_by(teacher_id = current_user.id)
	return render_template("tests.html", tests=tests)

@app.route('/tests/<int:id>', methods=['GET', 'POST'])
def test(id):
	test = Tests.query.get_or_404(id)
	return render_template('manage_test.html', test=test)

#lanjut kerja ini
@app.route('/tests/<int:id>/add-question', methods=['GET', 'POST'])
def add_question(id):
	test = Tests.query.get_or_404(id)
	return render_template('tests.html', test=test)

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