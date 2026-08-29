#!/bin/bash

echo "------------------------------------------"
echo "Building the project..."
echo "------------------------------------------"

echo "------------------------------------------"
echo " Installing npm..."
echo "------------------------------------------"
npm ci
npm install
npm run build

echo "------------------------------------------"
echo "Setting up Python venv..."
echo "------------------------------------------"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn

echo "------------------------------------------"
echo "Setting up backend..."
echo "------------------------------------------"
nohup uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 > uvicorn.log 2>&1 &

echo "------------------------------------------"
echo "Installation Complete!"
echo "------------------------------------------"

echo "------------------------------------------"
echo "To run enter this command: npm run dev"
echo "------------------------------------------"
