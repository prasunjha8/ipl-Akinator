#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Install dependencies if needed
# pip install -r requirements.txt

# Start FastAPI backend in the background
echo "Starting FastAPI backend..."
uvicorn api:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run app.py

# When Streamlit is closed, kill the backend
kill $BACKEND_PID
