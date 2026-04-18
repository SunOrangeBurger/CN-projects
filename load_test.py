"""
Load test for Quiz Network
Simulates multiple concurrent users joining a room and answering questions
"""

import socketio
import requests
import time
import threading
import random
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
NUM_USERS = 5  # Number of simulated users (reduced for testing)
ROOM_CODE = None  # Will be set after creating room

class QuizUser:
    def __init__(self, user_id):
        self.user_id = user_id
        self.username = f"loadtest_{int(time.time())}_{user_id}"
        self.password = "test123"
        self.session = requests.Session()
        self.sio = socketio.Client()
        self.latencies = []
        self.answers_submitted = 0
        
    def register_and_login(self):
        """Register and login the user"""
        # Register
        reg_response = self.session.post(f"{BASE_URL}/register", data={
            'username': self.username,
            'password': self.password
        }, allow_redirects=False)
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/login", data={
            'username': self.username,
            'password': self.password
        }, allow_redirects=False)
        
        success = login_response.status_code in [200, 302]
        if not success:
            print(f"[{self.username}] Login failed with status {login_response.status_code}")
        
        return success
    
    def connect_socket(self):
        """Connect to Socket.IO with session cookies"""
        try:
            cookies = self.session.cookies.get_dict()
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
            
            self.sio.connect(BASE_URL, headers={'Cookie': cookie_str}, wait_timeout=10)
            
            # Setup event handlers
            self.sio.on('quiz_started', self.on_quiz_started)
            self.sio.on('question_data', self.on_question_data)
            self.sio.on('user_finished', self.on_user_finished)
            self.sio.on('quiz_ended', self.on_quiz_ended)
            self.sio.on('leaderboard_data', self.on_leaderboard_data)
            
            return True
        except Exception as e:
            print(f"[{self.username}] Socket connection failed: {e}")
            return False
        
    def join_room(self, room_code):
        """Join a quiz room"""
        self.sio.emit('join', {'room': room_code})
        print(f"[{self.username}] Joined room {room_code}")
        
    def on_quiz_started(self, data):
        """Handle quiz start event"""
        print(f"[{self.username}] Quiz started, requesting first question...")
        # Request first question
        self.sio.emit('get_question', {'room': ROOM_CODE})
    
    def on_question_data(self, data):
        """Handle receiving a question"""
        question = data['question']
        index = data['index']
        total = data['total']
        print(f"[{self.username}] Question {index+1}/{total}: {question['text'][:50]}...")
        
        # Simulate thinking time (random 1-5 seconds)
        think_time = random.uniform(1, 5)
        time.sleep(think_time)
        
        # Submit answer
        self.submit_answer(question)
    
    def on_user_finished(self, data):
        """Handle user finishing all questions"""
        print(f"[{self.username}] Finished all questions! Requesting leaderboard...")
        self.sio.emit('get_leaderboard', {'room': ROOM_CODE})
    
    def on_leaderboard_data(self, data):
        """Handle receiving leaderboard data"""
        leaderboard = data['leaderboard']
        my_position = next((i+1 for i, entry in enumerate(leaderboard) if entry['username'] == self.username), None)
        if my_position:
            print(f"[{self.username}] Current position: #{my_position}")
        
    def submit_answer(self, question):
        """Submit an answer to the current question"""
        # Measure latency
        start = time.time()
        
        # Choose answer based on question type
        if question['type'] == 'mcq':
            answer = random.choice(['A', 'B', 'C', 'D'])
        elif question['type'] == 'truefalse':
            answer = random.choice(['true', 'false'])
        else:
            answer = "test answer"
        
        latency = random.uniform(10, 100)  # Simulate network latency
        
        self.sio.emit('submit_answer', {
            'room': ROOM_CODE,
            'answer': answer,
            'latency': latency,
            'responseTime': time.time() - start
        })
        
        self.answers_submitted += 1
        self.latencies.append(latency)
        print(f"[{self.username}] Submitted answer: {answer} (latency: {latency:.2f}ms)")
        
    def on_quiz_ended(self, data):
        """Handle quiz end event"""
        print(f"[{self.username}] Quiz ended. Submitted {self.answers_submitted} answers")
        
    def disconnect(self):
        """Disconnect from server"""
        if self.sio.connected:
            self.sio.disconnect()


def create_host_and_quiz():
    """Create a host user, quiz, and room"""
    print("\n=== Setting up host and quiz ===")
    
    session = requests.Session()
    
    # Register host
    session.post(f"{BASE_URL}/register", data={
        'username': 'host_user',
        'password': 'host123'
    })
    
    # Login host
    session.post(f"{BASE_URL}/login", data={
        'username': 'host_user',
        'password': 'host123'
    })
    
    # Create quiz
    questions = [
        {
            'text': 'What is 2 + 2?',
            'type': 'mcq',
            'options': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
            'correct': 'B',
            'timeLimit': 30
        },
        {
            'text': 'Is Python a programming language?',
            'type': 'truefalse',
            'correct': 'true',
            'timeLimit': 20
        },
        {
            'text': 'What is the capital of France?',
            'type': 'text',
            'correct': 'Paris',
            'timeLimit': 25
        }
    ]
    
    import json
    response = session.post(f"{BASE_URL}/create_quiz", data={
        'title': 'Load Test Quiz',
        'questions': json.dumps(questions)
    })
    
    # Get quiz ID from dashboard
    dashboard = session.get(f"{BASE_URL}/dashboard")
    
    # Create room (assuming quiz_id = 1 for simplicity)
    response = session.get(f"{BASE_URL}/create_room/1", allow_redirects=False)
    
    # Extract room code from redirect
    if response.status_code == 302:
        location = response.headers['Location']
        room_code = location.split('/')[-1]
        print(f"Created room with code: {room_code}")
        return session, room_code
    
    return None, None


def simulate_user(user_id, room_code, start_event):
    """Simulate a single user"""
    try:
        user = QuizUser(user_id)
        
        # Register and login
        if not user.register_and_login():
            print(f"[{user.username}] Failed to login")
            return
        
        # Connect to Socket.IO
        if not user.connect_socket():
            print(f"[{user.username}] Failed to connect socket")
            return
        
        # Wait for all users to be ready
        start_event.wait()
        
        # Join room
        user.join_room(room_code)
        
        # Keep connection alive for quiz duration
        time.sleep(60)  # 1 minute
        
        # Disconnect
        user.disconnect()
        
        print(f"[{user.username}] Test completed. Avg latency: {sum(user.latencies)/len(user.latencies) if user.latencies else 0:.2f}ms")
        
    except Exception as e:
        print(f"[user_{user_id}] Error: {e}")
        import traceback
        traceback.print_exc()


def run_load_test():
    """Run the load test"""
    global ROOM_CODE
    
    print("=" * 60)
    print("QUIZ NETWORK LOAD TEST")
    print("=" * 60)
    print(f"Simulating {NUM_USERS} concurrent users")
    print(f"Target: {BASE_URL}")
    print("=" * 60)
    
    # Create host and quiz
    host_session, room_code = create_host_and_quiz()
    
    if not room_code:
        print("Failed to create room. Make sure the server is running.")
        return
    
    ROOM_CODE = room_code
    
    # Create start event for synchronization
    start_event = threading.Event()
    
    # Create user threads
    threads = []
    print(f"\n=== Creating {NUM_USERS} simulated users ===")
    
    start_time = time.time()
    
    for i in range(NUM_USERS):
        thread = threading.Thread(target=simulate_user, args=(i, room_code, start_event))
        thread.start()
        threads.append(thread)
        time.sleep(0.1)  # Stagger connection attempts
    
    print(f"\n=== All users created. Starting test... ===\n")
    
    # Wait a bit for all connections
    time.sleep(2)
    
    # Signal all users to start
    start_event.set()
    
    # Start the quiz from host
    print("\n=== Starting quiz ===")
    host_sio = socketio.Client()
    cookies = host_session.cookies.get_dict()
    cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
    host_sio.connect(BASE_URL, headers={'Cookie': cookie_str})
    host_sio.emit('join', {'room': room_code})
    time.sleep(1)
    host_sio.emit('start_quiz', {'room': room_code})
    
    # Wait for users to complete questions (users progress independently)
    print("\n=== Users answering questions independently ===")
    time.sleep(30)  # Give users time to answer all questions
    
    # End quiz
    print("\n=== Ending quiz ===")
    host_sio.emit('end_quiz', {'room': room_code})
    
    # Wait for all threads to complete
    print("\n=== Waiting for all users to complete ===")
    for thread in threads:
        thread.join(timeout=30)
    
    host_sio.disconnect()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("LOAD TEST COMPLETED")
    print("=" * 60)
    print(f"Total duration: {duration:.2f} seconds")
    print(f"Users simulated: {NUM_USERS}")
    print(f"Room code: {room_code}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_load_test()
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
    except Exception as e:
        print(f"\n\nLoad test failed: {e}")
        import traceback
        traceback.print_exc()
