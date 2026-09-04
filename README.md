# sweng861-crud-tpz5005
Thomas Zimmerman

SWENG861 - Software Construction

## Project
Project M: Campus Treasury 
This project is a tool used by clubs to submit budget proposals. The proposals are then evaluated, and approved/rejected 
based on amount requested and available funds.

## Authentication Strategy
For this assignemnt, I implemented the Option A strategy for authentication. I chose this strategy becuase I believe it is the most applicable for my project. Near the top of the page, the user will see a 'Log in with GitHub' button. With this button they will be prompted to authenticate with their GitHub account (same log in process as logging into GitHub). After they have logged in, endpoint that require authentication will be accessable.

## Protected Endpoint Description
For this assignment, I protected endpoint /api/hello. This endpoint cannot be acccessed until after the user has logged in with GitHub. The endpoint functions in this way: Before logging in the endpoint will attempt to get information, but becuase no authentication token is recognized, it will throw a 401 error. The user will then log in with GitHub. After the log in process the endpoint will check the available token, and if valid, return the information in its respective function.

## OWASP Practices
- Limited client interactions with /auth/login endpoint

- Enapsulated authentication so that attacker cannot attack object-level authorization

- Implemented a basic logger and exception handler for server exceptions

## Tech Stack
-Node.js

-React

-Vite

-FastAPI

-MySQL

## How to clone
git clone git@github.com:psu-edu/sweng861-crud-tpz5005.git

## How to Build
cd sweng861-crud-tpz5005/

source build.sh

## How to launch python venv
source .venv/bin/activate

## How to run
npm run start-all
