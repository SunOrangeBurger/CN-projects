from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Quiz, Room, Participant, Answer
import secrets
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    rooms = Room.query.filter_by(host_id=current_user.id, status='waiting').all()
    return render_template('dashboard.html', quizzes=quizzes, rooms=rooms)

@app.route('/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if request.method == 'POST':
        title = request.form.get('title')
        questions_json = request.form.get('questions')
        
        quiz = Quiz(title=title, creator_id=current_user.id, questions_json=questions_json)
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('create_quiz.html')

@app.route('/create_room/<int:quiz_id>')
@login_required
def create_room(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    code = secrets.token_urlsafe(6)[:6].upper()
    
    room = Room(code=code, quiz_id=quiz_id, host_id=current_user.id)
    db.session.add(room)
    db.session.commit()
    
    return redirect(url_for('room', code=code))

@app.route('/room/<code>')
@login_required
def room(code):
    room = Room.query.filter_by(code=code).first_or_404()
    quiz = db.session.get(Quiz, room.quiz_id)
    is_host = room.host_id == current_user.id
    
    participant = Participant.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if not participant and not is_host:
        if room.status != 'waiting':
            flash('Room is locked')
            return redirect(url_for('dashboard'))
        participant = Participant(room_id=room.id, user_id=current_user.id)
        db.session.add(participant)
        db.session.commit()
    
    return render_template('room.html', room=room, quiz=quiz, is_host=is_host)

@socketio.on('join')
def on_join(data):
    room_code = data['room']
    join_room(room_code)
    room = Room.query.filter_by(code=room_code).first()
    
    participants = Participant.query.filter_by(room_id=room.id).all()
    participant_list = [{'username': db.session.get(User, p.user_id).username, 'score': p.score} for p in participants]
    
    emit('user_joined', {'username': current_user.username, 'participants': participant_list}, room=room_code)

@socketio.on('start_quiz')
def start_quiz(data):
    room_code = data['room']
    room = Room.query.filter_by(code=room_code).first()
    
    if room.host_id != current_user.id:
        return
    
    room.status = 'active'
    room.current_question = 0
    db.session.commit()
    
    quiz = db.session.get(Quiz, room.quiz_id)
    questions = quiz.get_questions()
    
    emit('quiz_started', {'question': questions[0], 'index': 0, 'total': len(questions)}, room=room_code)

@socketio.on('submit_answer')
def submit_answer(data):
    room_code = data['room']
    answer_text = data['answer']
    latency = data['latency']
    
    room = Room.query.filter_by(code=room_code).first()
    
    # Don't allow host to submit answers
    if room.host_id == current_user.id:
        return
    
    quiz = db.session.get(Quiz, room.quiz_id)
    questions = quiz.get_questions()
    current_q = questions[room.current_question]
    
    is_correct = str(answer_text).strip().lower() == str(current_q['correct']).strip().lower()
    
    answer = Answer(
        room_id=room.id,
        user_id=current_user.id,
        question_index=room.current_question,
        answer=answer_text,
        latency=latency,
        is_correct=is_correct
    )
    db.session.add(answer)
    
    if is_correct:
        participant = Participant.query.filter_by(room_id=room.id, user_id=current_user.id).first()
        if participant:
            participant.score += 1
    
    db.session.commit()
    
    emit('answer_submitted', {'username': current_user.username}, room=room_code)

@socketio.on('next_question')
def next_question(data):
    room_code = data['room']
    room = Room.query.filter_by(code=room_code).first()
    
    if room.host_id != current_user.id:
        return
    
    quiz = db.session.get(Quiz, room.quiz_id)
    questions = quiz.get_questions()
    
    room.current_question += 1
    db.session.commit()
    
    if room.current_question < len(questions):
        emit('quiz_started', {
            'question': questions[room.current_question],
            'index': room.current_question,
            'total': len(questions)
        }, room=room_code)
    else:
        end_quiz({'room': room_code})

@socketio.on('end_quiz')
def end_quiz(data):
    room_code = data['room']
    room = Room.query.filter_by(code=room_code).first()
    
    if room.host_id != current_user.id:
        return
    
    room.status = 'finished'
    db.session.commit()
    
    participants = Participant.query.filter_by(room_id=room.id).all()
    leaderboard = []
    
    for p in participants:
        user = db.session.get(User, p.user_id)
        answers = Answer.query.filter_by(room_id=room.id, user_id=p.user_id).all()
        avg_latency = sum(a.latency for a in answers) / len(answers) if answers else 0
        
        leaderboard.append({
            'username': user.username,
            'score': p.score,
            'avg_latency': round(avg_latency, 2)
        })
    
    leaderboard.sort(key=lambda x: (-x['score'], x['avg_latency']))
    
    emit('quiz_ended', {'leaderboard': leaderboard}, room=room_code)

@socketio.on('get_latency_data')
def get_latency_data(data):
    room_code = data['room']
    room = Room.query.filter_by(code=room_code).first()
    
    answers = Answer.query.filter_by(room_id=room.id).all()
    latencies = []
    
    for a in answers:
        user = db.session.get(User, a.user_id)
        latencies.append({
            'username': user.username,
            'latency': round(a.latency, 2),
            'timestamp': a.answered_at.strftime('%H:%M:%S')
        })
    
    avg_latency = sum(a.latency for a in answers) / len(answers) if answers else 0
    
    emit('latency_data', {'latencies': latencies, 'avg': round(avg_latency, 2)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
