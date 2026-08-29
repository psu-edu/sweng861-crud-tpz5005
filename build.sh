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
pip install -r requirements.txt

echo "------------------------------------------"
echo "Installation Complete!"
echo "------------------------------------------"

echo "------------------------------------------"
echo "To run enter this command: npm run dev"
echo "------------------------------------------"
