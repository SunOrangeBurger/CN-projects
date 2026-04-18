# Quiz Network

A real-time multiplayer quiz platform built with Flask, Socket.IO, and SQLite.

## Features

- User authentication and account management
- Create custom quizzes with MCQ, True/False, and text questions
- Host quiz rooms with shareable codes
- Real-time quiz gameplay with WebSocket support
- Network latency tracking with ping-pong measurement
- Live leaderboard with tiebreaker based on latency-adjusted time
- Neon red and gunmetal grey themed UI
- Admin/host monitoring dashboard with latency graphs

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The app will run on `http://0.0.0.0:5000`

### 3. Using with ngrok

To make the app accessible over the internet:

1. Install ngrok: https://ngrok.com/download
2. Run ngrok:
```bash
ngrok http 5000
```
3. Share the ngrok URL with participants

## Usage

1. **Register/Login**: Create an account or login
2. **Create Quiz**: Build a quiz with at least one question
3. **Open Room**: Create a room from your quiz
4. **Share Code**: Share the 6-character room code with participants
5. **Start Quiz**: Once participants join, start the quiz
6. **Monitor**: Hosts can view latency graphs and individual participant latencies
7. **Results**: View final leaderboard with scores and average latencies

## Load Testing

Two load test scripts are provided:

### Simple Load Test
Tests basic endpoints and measures response times:
```bash
python simple_load_test.py
```

### Full Load Test
Simulates multiple concurrent users joining and playing a quiz:
```bash
python load_test.py
```

Edit the `NUM_USERS` variable in `load_test.py` to adjust the number of simulated users (default: 20).

## Database

The app uses SQLite (`quiz.db`) which is created automatically on first run.

## Tech Stack

- Backend: Flask, Flask-SocketIO, SQLAlchemy
- Frontend: HTML, CSS, JavaScript, Socket.IO client
- Database: SQLite
- Real-time: WebSocket via Socket.IO

## Architecture

- **Host/Admin**: Creates quizzes, opens rooms, controls quiz flow, monitors latency
- **Participants**: Join rooms, answer questions in real-time
- **Latency Measurement**: Ping-pong protocol measures actual network latency (not response time)
- **Scoring**: Correct answers earn points, ties broken by average latency

## Notes

- Rooms are locked once the quiz starts
- Hosts cannot answer questions (admin role only)
- Scoring is based on correct answers
- Tiebreakers use network latency measurements
- Latency is measured every 2 seconds via ping-pong
- Real-time updates via WebSocket ensure synchronized gameplay
