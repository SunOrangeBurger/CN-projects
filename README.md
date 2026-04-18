# Quiz Network

A real-time multiplayer quiz platform built with Flask, Socket.IO, and SQLite.

## Features

- User authentication and account management
- Create custom quizzes with MCQ, True/False, and text questions
- Host quiz rooms with shareable codes
- Real-time quiz gameplay with WebSocket support
- Latency tracking and monitoring for hosts
- Live leaderboard with tiebreaker based on latency-adjusted time
- Neon red and gunmetal grey themed UI

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

## Database

The app uses SQLite (`quiz.db`) which is created automatically on first run.

## Tech Stack

- Backend: Flask, Flask-SocketIO, SQLAlchemy
- Frontend: HTML, CSS, JavaScript, Socket.IO client
- Database: SQLite
- Real-time: WebSocket via Socket.IO

## Notes

- Rooms are locked once the quiz starts
- Scoring is based on correct answers
- Tiebreakers use latency-adjusted response time
- Hosts can monitor real-time latency data
