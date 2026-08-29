#!/bin/bash

echo "------------------------------------------"
echo "Building the project..."
echo "------------------------------------------"

echo "------------------------------------------"
echo " Installing npm..."
echo "------------------------------------------"
npm ci
npm install

echo "------------------------------------------"
echo "Setting up Python venv..."
echo "------------------------------------------"
apt install python3-pip -y python3-venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "------------------------------------------"
echo "Installation Complete!"
echo "------------------------------------------"

echo "------------------------------------------"
echo "To run enter this command: npm run dev"
echo "------------------------------------------"
