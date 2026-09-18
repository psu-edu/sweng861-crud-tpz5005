#!/bin/bash

echo "------------------------------------------"
echo "Preparing Environment..."
echo "------------------------------------------"

# Generate local SSL certificates
if [ ! -f "backend/cert.pem" ] || [ ! -f "backend/key.pem" ]; then
    echo "No SSL certificates found. Generating local certs for development..."
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out backend/cert.pem -keyout backend/key.pem \
        -days 365 -subj "/CN=localhost"
else
    echo "SSL certificates already exist. Skipping generation."
fi

echo "------------------------------------------"
echo "Building with Docker..."
echo "------------------------------------------"
docker-compose build --no-cache

echo "------------------------------------------"
echo "Building Complete!"
echo "-----"
echo "To start the application... "
echo "enter this command: docker-compose up"
echo "-----"
echo "To open the project, hold Control and"
echo "click the link 'https://localhost:3000/'"
echo "------------------------------------------"



