from flask import Flask, render_template, flash, request, redirect, url_for
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, ValidationError, IntegerField, RadioField, DateTimeLocalField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, EqualTo, Length, Optional
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user
from functools import wraps
import secrets
from apscheduler.schedulers.background import BackgroundScheduler





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

def login_required(role="ANY"):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):

            if not current_user.is_authenticated:
               return login_manager.unauthorized()
            if ( (current_user.role != role) and (role != "ANY")):
                return login_manager.unauthorized()      
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper



#create model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique =True)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    # submissions object in the users
    submissions = db.relationship('Submission', backref='submitted_tests', lazy=True)


class Tests(db.Model):
    test_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    start_date = db.Column(db.DateTime, nullable = False)
    end_date = db.Column(db.DateTime, nullable = False)
    status = db.Column(db.String(255))
    # Foreign Key To Link User (refer to primary key of the user)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # teacher object associated to the test
    teacher = db.relationship('Users', backref=db.backref('tests', lazy=True))
    # list of questions from the questions table
    questions = db.relationship("Questions", backref="question_list")
    code = db.Column(db.String(6), unique=True)  # column to store the unique code
    # students object in the test
    students = db.relationship('Users', secondary='test_students', backref=db.backref('tests_registered', lazy=True))
    # submissions object in the test
    submissions = db.relationship('Submission', backref='test_submissions', lazy=True)


     
class Questions(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(255), nullable=False)
    question_type = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    option1 = db.Column(db.String(255))
    option2 = db.Column(db.String(255))
    option3 = db.Column(db.String(255))
    option4 = db.Column(db.String(255))
    correct_opt = db.Column(db.Integer)
    correct_ans = db.Column(db.String(255))
    stt = db.Column(db.Boolean)
	# Foreign Key To Link test (refer to primary key of the test)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.test_id'))
    # test object related to the question
    test = db.relationship('Tests', backref=db.backref('question_test', lazy=True))
    #one-to-one relationship with the Answer model
    answer = db.relationship("Answers", uselist=False)

class Answers(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(255))
    result = db.Column(db.Boolean, nullable=False) 
    chosen_opt = db.Column(db.Integer)
    points_gained = db.Column(db.Integer)
    similarity_score = db.Column(db.Float)
	# Foreign Key To Link to question (refer to primary key of the question)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'))
    # Foreign Key To Link to users(student) (refer to primary key of the user)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # student object associated with the answer
    student = db.relationship('Users', backref=db.backref('answers', lazy=True))
    # Foreign Key To Link to submissions (refer to primary key of the submission)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.submission_id'))
    submission = db.relationship('Submission', backref=db.backref('answer', lazy=True))

class Submission(db.Model):
    submission_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    test_id = db.Column(db.Integer, db.ForeignKey('tests.test_id'))
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    total_points = db.Column(db.Integer)
    student = db.relationship('Users', backref=db.backref('submitter', lazy=True))
    test = db.relationship('Tests', backref=db.backref('submission_test', lazy=True))
    answers = db.relationship('Answers', backref=db.backref('answered_questions', lazy=True), lazy=True)

test_students = db.Table('test_students',
                         db.Column('test_id', db.Integer, db.ForeignKey('tests.test_id'), primary_key=True),
                         db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True))
    
# Create database within app context
with app.app_context():
    db.create_all()

# Create a scheduler
scheduler = BackgroundScheduler()

# Define a function to update test status
def update_test_status():
    with app.app_context():
        tests = Tests.query.all()
        current_time = datetime.now()
        for test in tests:
            if test.start_date <= current_time < test.end_date:
                test.status = 'ongoing'
            elif current_time >= test.end_date:
                test.status = 'finished'
        db.session.commit()

# Add the job to the scheduler
scheduler.add_job(func=update_test_status, trigger="interval", seconds=60)  # Run every 60 seconds

# Start the scheduler
scheduler.start()

# create registration form
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(),])
    role = RadioField('Role', choices=[('student', 'student'), 
                                                         ('teacher', 'teacher')], validators=[DataRequired()])
    submit = SubmitField("Register")

# create login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(),])
    submit = SubmitField("Login")

# create enter-code form
class CodeForm(FlaskForm):
    code = StringField("Code", validators=[DataRequired()])
    submit = SubmitField("Submit")

# create create-test form
class TestForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    start_date = DateTimeLocalField('Start_date', validators=[DataRequired()])
    end_date = DateTimeLocalField("End_date", validators=[DataRequired()])
    submit = SubmitField("Submit")

class QuestionForm(FlaskForm):
    question_text = StringField('Question Text', validators=[DataRequired()])
    question_type = RadioField('Question Type', choices=[('multiple-choice', 'Multiple Choice'), ('essay', 'Essay')], validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired()]) 
   
    # Multiple Choice fields
    option1 = StringField('Option 1')
    option2 = StringField('Option 2')
    option3 = StringField('Option 3')
    option4 = StringField('Option 4')
    correct_opt = IntegerField('Correct Option', validators=[Optional()])
   
    # Essay field
    correct_ans = TextAreaField('Correct Answer')
    stt = RadioField('Speech to text', choices=[(True, 'Yes'), (False, 'No')], validators=[Optional()])

    submit = SubmitField("Submit")

    def validate_correct_ans(self, field):
        if self.question_type.data == 'essay' and not field.data:
            raise ValidationError('This field is required')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Users(name=form.name.data, email=form.email.data, password=form.password.data, role = form.role.data)
            db.session.add(user)
            db.session.commit()
            form.name.data = ''
            form.password.data = ''
            form.email.data = ''
            form.role.data = ''
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
            if (user.password == form.password.data):
                if (user.role == "teacher"):
                    login_user(user)
                    flash("Login Succesfull!!")
                    return redirect(url_for('teacher_dashboard'))
                else:
                    login_user(user)
                    flash("Login Succesfull!!")
                    return redirect(url_for('student_dashboard'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn't Exist! Try Again...")
        
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required(role="ANY")
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))

@app.route('/create-test', methods=['GET', 'POST'])
@login_required(role="teacher")
def create_test():
    form = TestForm()
    if form.validate_on_submit():
        creator = current_user.id
        current_time = datetime.now()
        if form.start_date.data < current_time:
            # Return error Message
            flash("Cannot set start date before the current time")
            return redirect(url_for('create_test'))  
        elif form.end_date.data < form.start_date.data:
            # Return error Message
            flash("Cannot set end date before the start date")
            return redirect(url_for('create_test'))  

        code = secrets.token_hex(3)  # generate a random 6-digit code
        test = Tests(title=form.title.data, start_date=form.start_date.data, end_date=form.end_date.data, teacher_id=creator, code=code, teacher = current_user)
		# Clear The Form
        form.title.data = ''
        form.start_date.data = ''
        form.end_date.data = ''

        test.status = 'scheduled'

		# Add test data to database
        db.session.add(test)
        db.session.commit()

		# Return a Message
        flash("Test Created Successfully!")
        return redirect(url_for('tests'))

	# Redirect to the webpage 
    return render_template("create_test.html", form=form)

@app.route('/tests', methods=['GET', 'POST'])
@login_required(role="teacher")
def tests():
    # Grab all the tests by the teacher from the database
	tests = Tests.query.filter_by(teacher_id = current_user.id)
	return render_template("tests.html", tests=tests)

@app.route('/tests/<int:id>', methods=['GET', 'POST'])
@login_required(role="teacher")
def test(id):
    test = Tests.query.get_or_404(id)
    questions = Questions.query.filter_by(test_id = id)
    return render_template('manage_test.html', test=test, questions=questions)

@app.route('/tests/<int:id>/add-question', methods=['GET', 'POST'])
@login_required(role="teacher")
def add_question(id):
    form = QuestionForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            test = Tests.query.get_or_404(id)
            ## Create a new question object and save it to the database
            question = Questions(question_text=form.question_text.data, 
                                question_type=form.question_type.data, 
                                points=form.points.data, 
                                test_id = id, test = test)

            if form.question_type.data == 'multiple-choice':
                question.option1 = form.option1.data
                question.option2 = form.option2.data
                question.option3 = form.option3.data
                question.option4 = form.option4.data
                question.correct_opt = form.correct_opt.data

            else:
                question.correct_ans = form.correct_ans.data
                question.stt = form.stt.data == 'True'

            test.questions.append(question)

            db.session.add(question)
            db.session.commit()
            flash('Question created successfully!')
            return redirect(url_for('test', id=id))
    return render_template('add_question.html', form=form, id = id)

@app.route('/tests/<int:id>/delete-test', methods=['GET', 'POST'])
@login_required(role="teacher")
def delete_test(id):
    test_to_delete = Tests.query.get_or_404(id)
    try:
        db.session.delete(test_to_delete)
        db.session.commit()

	    # Return a message
        flash("test Was Deleted!")
        return redirect(url_for('tests'))
    
    except:
        # Return an error message
        flash("Delete failed")
        return redirect(url_for('test', id=id))
    
@app.route('/tests/<int:id>/edit-test', methods=['GET', 'POST'])
@login_required(role="teacher")
def edit_test(id):
    test_to_edit = Tests.query.get_or_404(id)
    form = TestForm()
    if form.validate_on_submit():

        current_time = datetime.now()
        if form.start_date.data < current_time:
            # Return error Message
            flash("Cannot set start date before the current time")
            return redirect(url_for('create_test'))  
        elif form.end_date.data < form.start_date.data:
            # Return error Message
            flash("Cannot set end date before the start date")
            return redirect(url_for('create_test'))  

        test_to_edit.title = form.title.data
        test_to_edit.start_date = form.start_date.data
        test_to_edit.end_date = form.end_date.data
		# Update Database
        db.session.commit()
        flash("test Has Been Updated!")
        return redirect(url_for('test', id=id))

    if current_user.id == test_to_edit.teacher_id:
        form.title.data = test_to_edit.title
        form.start_date.data = test_to_edit.start_date
        form.end_date.data = test_to_edit.end_date
        return render_template('edit_test.html', form=form)
    
    else:
        flash("not authorized")
        return redirect(url_for('tests'))
    
@app.route('/tests/<int:id>/<int:question_id>/delete-question', methods=['GET', 'POST'])
@login_required(role="teacher")
def delete_question(id, question_id):
    question_to_delete = Questions.query.get_or_404(question_id)
    test = Tests.query.get_or_404(id)
    try:
        # Remove the question from the test's questions field
        test.questions.remove(question_to_delete)

        db.session.delete(question_to_delete)
        db.session.commit()

	    # Return a message
        flash("question Was Deleted!")
        return redirect(url_for('test', id=id))
    
    except:
        # Return an error message
        flash("Delete failed")
        return redirect(url_for('test', id=id))

@app.route('/tests/<int:id>/submission/<int:submission_id>/delete-submission', methods=['GET', 'POST'])
@login_required(role="teacher")
def delete_submission(id, submission_id):
    submission_to_delete = Submission.query.get_or_404(submission_id)
    test = Tests.query.get_or_404(id)
    try:
        # Remove the question from the test's questions field
        test.submissions.remove(submission_to_delete)

        db.session.delete(submission_to_delete)
        db.session.commit()

	    # Return a message
        flash("submission Was Deleted!")
        return redirect(url_for('test', id=id))
    
    except:
        # Return an error message
        flash("Delete failed")
        return redirect(url_for('test', id=id))

@app.route('/tests/<int:id>/<int:question_id>/edit-question', methods=['GET', 'POST'])
@login_required(role="teacher")
def edit_question(id, question_id):
    question_to_edit = Questions.query.get_or_404(question_id)
    form = QuestionForm()
    if form.validate_on_submit():
        if form.question_type.data == 'multiple-choice':
            question_to_edit.question_text = form.question_text.data
            question_to_edit.question_type = form.question_type.data
            question_to_edit.points = form.points.data
            
            question_to_edit.option1 = form.option1.data
            question_to_edit.option2 = form.option2.data
            question_to_edit.option3 = form.option3.data
            question_to_edit.option4 = form.option4.data
            question_to_edit.correct_opt = form.correct_opt.data
            # Update Database
            db.session.add(question_to_edit)
            db.session.commit()
            flash("question Has Been Updated!")
            return redirect(url_for('test', id=id))
        
        elif form.question_type.data == 'essay':
            question_to_edit.question_text = form.question_text.data
            question_to_edit.question_type = form.question_type.data
            question_to_edit.points = form.points.data

            question_to_edit.correct_ans = form.correct_ans.data
            question_to_edit.stt = form.stt.data == 'True'

            # Update Database
            db.session.add(question_to_edit)
            db.session.commit()
            flash("question Has Been Updated!")
            return redirect(url_for('test', id=id))
        
        else:
            flash("edit failed")
            return redirect(url_for('edit_question', id=id, question_id = question_id))
    else:
        form.question_text.data = question_to_edit.question_text
        form.question_type.data = question_to_edit.question_type
        form.points.data = question_to_edit.points
        if question_to_edit.question_type == 'multiple-choice':
            form.option1.data = question_to_edit.option1
            form.option2.data = question_to_edit.option2
            form.option3.data = question_to_edit.option3
            form.option4.data = question_to_edit.option4
            form.correct_opt.data = question_to_edit.correct_opt
            return render_template('edit_question.html', form=form, question = question_to_edit)
        elif question_to_edit.question_type == 'essay':
            form.correct_ans.data = question_to_edit.correct_ans
            return render_template('edit_question.html', form=form, question = question_to_edit)
        
@app.route('/student/enter-code', methods=['GET', 'POST'])
@login_required(role="student")
def enter_code():
    form = CodeForm()
    if form.validate_on_submit():
        code = form.code.data
        test = Tests.query.filter_by(code=code).first()
        if test:
            test.students.append(current_user)
            db.session.commit()
            flash("succesfully joined a test")
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid code")
            return redirect(url_for('enter_code'))
    return render_template('enter_code.html', form=form)

@app.route('/start-test/<int:test_id>', methods=['GET', 'POST'])
@login_required(role="student")
def start_test(test_id):
    test = Tests.query.get_or_404(test_id)
    questions = test.questions

    for submission in test.submissions:
        if submission.student_id == current_user.id:
            flash("You have already submitted this test")
            return redirect(url_for('student_dashboard'))

     # Check if the test is within the allowed duration
    current_time = datetime.now()
    if current_time < test.start_date or current_time > test.end_date:
        flash("Test is not available at this time.")
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        # Redirect to submit-test route to handle form submission
        flash("Test submitted")
        return redirect(url_for('submit_test', test_id = test_id))
    
    return render_template('start_test.html', test=test, questions=questions)

@app.route('/submit-test/<int:test_id>', methods=['POST'])
@login_required(role="student")
def submit_test(test_id):
    test = Tests.query.get_or_404(test_id)
    questions = test.questions

    # Create a new Submission object
    submission = Submission(student_id=current_user.id, test_id=test_id, 
                            student = current_user, test = test)
    db.session.add(submission)
    db.session.commit()

    # Create a list to store the answers
    answers = []

    #initiate model
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    #total score
    total_points = 0

    # Iterate over the questions and get the user's answers
    for question in questions:

        # Check if the question is multiple-choice or essay
        if question.question_type == 'multiple-choice':
            correct_option = question.correct_opt
            chosen_opt = request.form.get(f"chosen_opt_{question.question_id}")
            if chosen_opt is not None:
                chosen_opt = int(chosen_opt)

                if chosen_opt == correct_option:
                    result = True
                    points_gained = question.points
                    total_points = total_points + points_gained
                else:
                    result = False
                    points_gained = None
            else:
                result = False
                points_gained = None
            
            # Create an Answer object and add it to the list
            answer_obj = Answers(chosen_opt = chosen_opt, result=result, question_id=question.question_id, 
                                 student_id=current_user.id, student = current_user, points_gained = points_gained,
                                 submission_id=submission.submission_id, submission = submission)
            answers.append(answer_obj)

        elif question.question_type == 'essay':
            answer = request.form.get(f"answer_{question.question_id}")
            correct_answer = question.correct_ans
            if answer == correct_answer:
                result = True
                points_gained = question.points
                total_points = total_points + points_gained
            # else:
            #     result = False
            #     points_gained = None
            else:
                sentences = [correct_answer, answer]

                embeddings = model.encode(sentences)
                similarity_result = cosine_similarity([embeddings[0]], embeddings[1:])
                similarity_result = similarity_result.item()

                if similarity_result > 0.5:
                    result = True
                    points_gained = question.points
                    total_points = total_points + points_gained
                else:
                    result = False
                    points_gained = None

            # Create an Answer object and add it to the list
            answer_obj = Answers(answer_text = answer, result=result, question_id=question.question_id, 
                                 student_id=current_user.id, student = current_user, points_gained = points_gained,
                                 submission_id=submission.submission_id, submission = submission, similarity_score=similarity_result)
            answers.append(answer_obj)
        
    # Add the answers to the database
    submission.answers = answers # Add the answers to submission's answers field
    submission.total_points = total_points #add the total points to submission
    db.session.add_all(answers)
    db.session.commit()

    # Update the test status

    #debug purpose
    #submission_to_test1 = submission

    flash("Test submitted successfully!")
    #debug purpose
    #return render_template('debug_answers.html', answers=answers, submission = submission_to_test1)
    return redirect(url_for('student_dashboard'))

@app.route('/tests/<int:id>/submission/<int:submission_id>', methods=['GET', 'POST'])
@login_required(role="teacher")
def view_submission(id, submission_id):
    test = Tests.query.get_or_404(id)
    submission = Submission.query.get_or_404(submission_id)
    return render_template("view_submission.html", test = test, submission=submission)

@app.route('/tests/<int:id>/submission/<int:submission_id>/<int:answer_id>', methods=['GET', 'POST'])
@login_required(role="teacher")
def change_result(id, submission_id, answer_id):
    test = Tests.query.get_or_404(id)
    submission = Submission.query.get_or_404(submission_id)
    answer_to_update = Answers.query.get_or_404(answer_id)
    question = Questions.query.get_or_404(answer_to_update.question_id)

    if answer_to_update.result == True:
        answer_to_update.result = False
        answer_to_update.points_gained = 0
        submission.total_points = submission.total_points - question.points
    else:
        answer_to_update.result = True
        answer_to_update.points_gained = question.points
        submission.total_points = submission.total_points + question.points
       

    #update database
    db.session.add(answer_to_update)
    db.session.commit()
    return render_template("view_submission.html", test = test, submission=submission)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        form = RegisterForm()
        return redirect(url_for('login'))

@app.route('/teacher', methods=['GET', 'POST'])
@login_required(role="teacher")
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/student', methods=['GET', 'POST'])
@login_required(role="student")
def student_dashboard():
    # Grab all the tests registered by the student from the database
    tests = current_user.tests_registered
    return render_template('student_dashboard.html', tests=tests)



@app.route('/test-speech', methods=['GET', 'POST'])
def test_speech():
    return render_template('testing.html')



if __name__ == '__main__':
    app.run(debug=True)