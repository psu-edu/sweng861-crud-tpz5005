import os
import logging
import time
from fastapi import Depends, FastAPI, Request, Response, HTTPException, status, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, make_asgi_app
import jwt
import uvicorn
import pprint
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import httpx
import json
import sqlite3
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from database import handle_user_login_data, init_db, print_database_info, get_data_field
from osrsdatabase import init_osrs_db, create_item, read_item, update_item, delete_item, get_all_ids, delete_all_items
from custom_auth import valid_user, create_jwt_token, SECRET_KEY, ALGORITHM
from metrics import REQUEST_LATENCY, REQUEST_TOTAL, ITEMS_CREATED_TOTAL, metrics_app

from logger import logger, log_event

load_dotenv() # load keys into env

init_db()  # Initialize the database
init_osrs_db() # initialize the osrs database

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security object for custom authentication
security = HTTPBearer(auto_error=False)

# A gateway for OSRS database specific endpoints
router = APIRouter(
    prefix="/api/osrs/database",
    tags=["OSRS database gateway"]
)

# Create logger
# TODO: maybe astract this out to another script
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app = FastAPI(
    title="SWENG861 Assignment API",
    description="A front and backend server used to implement weekly assignments",
    version="0.3"
)

# For metrics
app.mount("/metrics", metrics_app)

# set up a limiter for log in
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authlib middleware
# @info: used to encrypt sessiond ata
app.add_middleware(SessionMiddleware, 
                   secret_key="secret_encryption_key",
                   same_site="lax",
                   https_only=True)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# activate the router
app.include_router(router)

# instantiate authentication object
oauth = OAuth()

# I will use github, as that is used commonly for SWENG861
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"})

@app.middleware("http")
#-------------------------------------------------------------------#
async def prometheus_metrics(request: Request, call_next):
#-------------------------------------------------------------------#
    # start the timer
    start_time = time.perf_counter()

    try:
        # call the endpoint
        response = await call_next(request)
    except Exception:
        # Record failed requests 
        route = request.scope.get("route")

        # if the route was identified
        if route:
            route_path = route.path
        else:
            route_path = request.url.path

        # calculat the time duration of the endpoint
        # being called
        duration = time.perf_counter() - start_time

        # add it to prometheus
        REQUEST_LATENCY.labels(
            method=request.method,
            route=route_path
        ).observe(duration)

        # record the request error
        REQUEST_TOTAL.labels(
            method=request.method,
            route=route_path,
            status="500"
        ).inc()

        # remember to raise an exception for fastAPI
        raise

    # FastAPI is finished with the request, so we can now determine who 
    # handles it
    route = request.scope.get("route")

    if route:
        route_path = route.path
    else:
        route_path = request.url.path

    # Again calculate the time spent processing the request
    duration = time.perf_counter() - start_time

    # Record request latency
    REQUEST_LATENCY.labels(
        method=request.method,
        route=route_path
    ).observe(duration)

    # Record request count
    REQUEST_TOTAL.labels(
        method=request.method,
        route=route_path,
        status=str(response.status_code)
    ).inc()

    return response


# Authentication verification helper function
#-------------------------------------------------------------------#
async def require_auth(request: Request,
                       auth: HTTPAuthorizationCredentials = Depends(security) ) -> dict:
#-------------------------------------------------------------------#
    # First check for a custom authentication token
    if auth and auth.credentials:
        try:
            payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                return {"user": username, "auth_type": "custom_jwt"}
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid JWT token")
    
    # If no custom token, check for GitHub
    user = request.session.get("user")

    # if its null/failure throw an error
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication access token is required")

    return user

#-------------------------------------------------------------------#
async def require_admin(current_user: dict = Depends(require_auth)) ->dict:
#-------------------------------------------------------------------#
    # If the user is not an admin
    if current_user.get("role") != "admin":
        # throw an error
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN,
                                    detail="Admin privlages required")
    
    return current_user

#-------------------------------------------------------------------#
def verify_owner_or_admin(current_user: dict, owner_id: int):
#-------------------------------------------------------------------#
    is_owner = current_user["id"] == owner_id
    is_admin = current_user.get("role") == "admin"

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to use this endpoint"
        )
        
    return current_user

# Exception handler for excessive log in attempts
@app.exception_handler(RateLimitExceeded)
#-------------------------------------------------------------------#
async def handle_login_rate_exception(request: Request, 
                                      exc: RateLimitExceeded):
#-------------------------------------------------------------------#
    # get some info from the client
    client_ip = request.client.host

    # log into
    logger.warning(f"Excessive login attempts from: {client_ip}")

    # pretty sure code 429 is the right one here
    return JSONResponse(
        status_code=429,
        content={"detail": "Endpoint rate limit exceeded!"}
    )


# @info: Validation function that checks if data exists and if its of 
#        type JSON
#-------------------------------------------------------------------#
async def validate_data(data):
#-------------------------------------------------------------------#
    # check if the data is null
    if data is None:
        return False

    if isinstance(data, (list, dict)) and len(data) == 0:
        return False
    
    # check if the data is in json format
    if isinstance(data, str):
        try:
            json.loads(data)
            return True
        except ValueError:
            return False

    # if its good, return true
    return True


#####################################################################


# Service Provider login
# @info: This is the endpoint that re-directs the user to the external
#        github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/login")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("5/minute") # Only 5 logins per minute
async def login(request: Request):
    req_id = getattr(request.state, "request_id", None)

    # This redirect origin MUST match the frontend origin, otherwise 
    # the cookies will NOT SET for the frontend!!!!!
    redirect_uri = "https://localhost:8000/auth/callback" 

    log_event(
        level="INFO", 
        event_name="github_auth", 
        message="GitHub OAuth2 Login", 
        request_id=req_id
    )
    
    return await oauth.github.authorize_redirect(request, redirect_uri)


# Recieving end from the eternal github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/callback")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def auth_callback(request: Request):
    try:
        # Ask github to validate the login token and return an 
        # authentication token
        auth_token = await oauth.github.authorize_access_token(request)

        # With the auth token, ask github for information about user
        response_type = await oauth.github.get("user", token=auth_token)
        profile_info = response_type.json()

        # Saving this for debug purposes
        # print("---------- PROFILE INFO ----------")
        # pprint.pprint(profile_info)
        # print("----------------------------------")

        # If the email is private, we need to explicitly ask for an email
        # to recover any information
        if not profile_info.get("email"):
            email_resp = await oauth.github.get("user/emails", token=auth_token)
            emails = email_resp.json()
            for email in emails:
                if email.get("primary") and email.get("verified"):
                    profile_info["email"] = email.get("email")
                    break

        # store data in session cookie
        db_user = handle_user_login_data(profile_info)

        # store user data in session coockie
        request.session["user"] = db_user

        # Debug display info
        request.session["user"] = {
            "id": profile_info.get("id"),
            "username": profile_info.get("login"),
            "name": profile_info.get("name"),
            "avatar_url": profile_info.get("avatar_url"),
            "role": db_user["role"]
        }

        # if we are susseccful, redirect back to the frontend
        return RedirectResponse(url="https://localhost:3000/")

    # Throw debug error
    except Exception as error:
        raise HTTPException(status_code=400, detail="ERROR: Authentication failed")

    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.post("/auth/custom")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def login_custom(response: Response, user_data: dict):
    username = user_data.get("username")
    password = user_data.get("password")
    
    # Check the credentials
    if not valid_user(username, password):
        # Log failed login attempts
        log_event(
            level="WARNING",
            event_name="custom_login_failed",
            message=f"Failed custom login attempt for user '{username}'",
            username=username,
            auth_provider="custom"
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    # Generate a token
    token = create_jwt_token(username)
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )

    # Log a successful login 
    log_event(
        level="INFO",
        event_name="auth_login_success",
        message=f"User '{username}' logged in successfully",
        username=username,
        auth_provider="custom"
    )
    
    return {
        "authenticated": True,
        "user": {"username": username},
        "access_token": token,
        "token_type": "bearer"
    }


# Logout user
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/logout")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def logout(request: Request):
    req_id = getattr(request.state, "request_id", None)
    user = request.session.get("user")
    username = user.get("username") if user else "unknown"

    request.session.clear()

    # Log the logout
    log_event(
        level="INFO",
        event_name="auth_logout",
        message=f"User '{username}' logged out",
        request_id=req_id,
        username=username
    )

    return RedirectResponse(url="https://localhost:3000/")


# Get active user data
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/user")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def get_active_user(request: Request):
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


# Authentication required
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/hello")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def get_hello(request: Request, user: dict = Depends(require_auth)):
 
    session_userInfo = request.session.get("user")
    username = session_userInfo.get("username")
    
    user_email = get_data_field(user_id=1, field_name="email")

    return {"message": f"Hello, {username}@{user_email}!"}


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/runescape/price")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def get_item_price(user: dict = Depends(require_auth)):

    # In the game, each item has a developer-set id
    # This item's id is 1333
    item_id=1333

    # In order to use Jagex's official servers, you have to pay
    # as an alternative i will use the offical wiki, which updates less often
    # and returns less info
    map_url = "https://prices.runescape.wiki/api/v1/osrs/mapping" 

    headers = {
        "User-Agent": "Penn-State-Student-Project"
    }

    async with httpx.AsyncClient() as client:
        # get a response from the Jagex servers
        response = await client.get(map_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code= response.status_code, detail="Failed to fetch OSRS data")

        # try to turn the response into a json
        data = response.json()

        # Validate the data
        await validate_data(data)

        item_data = {}

        #parse the master list of items
        for item in data:
            #find the one we're looking for
            if item.get("id") == item_id:
                item_data = item
                break

        name = item_data.get("name")
        id = item_data.get("id")
        price = item_data.get("value")
        current_user = user.get("username") or user.get("user")
        
        # insert it into the database
        create_item(item_id=id, 
                    item_name=name, 
                    item_value=price,
                    created_by=current_user)

        # print("---------- data INFO ----------")
        # pprint.pprint(item_data)
        # print("----------------------------------")

        # item_data = data.get("data", {}).get(str(item_id), {})

        return {
            "item": "Rune Scimitar",
            "id": item_id,
            "price": item_data
        }

# @info: OSRS database POST function
# @param item_id - the 4 digit itme id 
# @param item_name - the name of the item
# @param item_value - the current traded price of the 
#                     item
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.post("/create",
             summary="OSRS database Create endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#@limiter.limit("1/second") # Only 1 create every second
def osrs_database_create(request: Request,
                         item_id: int = Body(...), 
                         item_name: str = Body(...), 
                         item_value:int = Body(...),
                         user: dict = Depends(require_auth)):

    req_id = getattr(request.state, "request_id", None)
    created_by = user.get("username") or user.get("user")

    try:
        # Create the item
        create_item(item_id, item_name, item_value, created_by)

        ITEMS_CREATED_TOTAL.labels(
            created_by=created_by
        ).inc()

        # Log the successful creation
        log_event(
            level="INFO", 
            event_name="osrs_item_created",
            message=f"Created item ID {item_id} ({item_name})",
            request_id=req_id,
            item_id=item_id,
            item_name=item_name,
            item_value=item_value,
            created_by=created_by
        )

    # If the ID already exists
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Item with ID: {item_id} already in database"
        )
    # if something unknown happens
    except sqlite3.Error as err:
        # Log an error when creating
        log_event(
            level="ERROR", 
            event_name="database_error", 
            message=f"Database error during item creation: {str(err)}", 
            request_id=req_id, 
            error=str(err)
        )

        raise HTTPException(
            status_code=500,
            detail="Unexpected Error"
        )

    return {
        "status": "success",
        "message": "Successfully created item"
    }


# @info: Debug helper function to print the user
#        database content
# @param item_id - the 4 digit id of the item
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.get("/read/{item_id}",
            summary="OSRS database Read endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/seconds") # Only 1 read every second
def osrs_database_read(request: Request,
                       item_id: int, 
                       user: dict = Depends(require_auth)):
    req_id = getattr(request.state, "request_id", None)
    item = read_item(item_id)
    current_user = user.get("username") or user.get("user")

    # make sure it exists
    if not item:
        # Log a missing item
        log_event(
            level="WARNING",
            event_name="osrs_item_not_found",
            message=f"Item {item_id} was requested but does not exist",
            request_id=req_id,
            item_id=item_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="This item does not exist or has been deleted.")
    
    # Check to make sure the item is created by the current session user
    if item["created_by"] != current_user:
        # log an unauthorized read
        log_event(
            level="WARNING",
            event_name="osrs_unauthorized_access",
            message=f"User '{current_user}' attempted unauthorized access to item ID {item_id}",
            request_id=req_id,
            item_id=item_id,
            requested_by=current_user
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to view this item.")

    log_event(
        level="INFO",
        event_name="osrs_item_read",
        message=f"Retrieved item ID: {item_id}",
        request_id=req_id,
        item_id=item_id,
        requested_by=current_user
    )
    
    return item 


# @info: Update item in database endpoint
# @param item_id - the 4 digit item id 
# @param fields - the fields to be updated
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.put("/update/{item_id}",
            summary="OSRS database Update endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#@limiter.limit("1/5seconds") # Only 1 update every 5 seconds
def osrs_database_update(request: Request,
                         item_id: int, 
                         fields: dict = Body(...),
                         user: dict = Depends(require_auth)):
    req_id = getattr(request.state, "request_id", None)
    current_user = user.get("username") or user.get("user")
    current_item = read_item(item_id)

    # make sure it exists
    if not current_item:
        raise HTTPException(status_code=404, detail="Item not found in database")

    # if it does exist, update the data
    update_item(item_id, fields)

    # log an update
    log_event(
        level="INFO",
        event_name="osrs_item_updated",
        message=f"Updated item ID: {item_id}",
        request_id=req_id,
        item_id=item_id,
        updated_fields=list(fields.keys()),
        updated_by=current_user
    )

    return {
        "status": "success",
        "message": "Item's data successfully updated"
    } 


# @info: Delete endpoint for the OSRS database
# @param item_id - the 4 digit id 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.delete("/delete/{item_id}",
                summary="OSRS database Delete endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/seconds") # Only 1 delete every 5 seconds
def osrs_database_delete(request: Request,
                         item_id: int, 
                         user: dict = Depends(require_auth)):
    req_id = getattr(request.state, "request_id", None)
    current_user = user.get("username") or user.get("user")
    current_item = read_item(item_id)

    # it it doesnt exist, throw an error
    if not current_item:
        raise HTTPException(
            status_code=404,
            detail=f"Item with ID: {item_id} does not exist in OSRS database"
        )

    # if it does, delete it
    delete_item(item_id)

    # log a delete
    log_event(
        level="INFO",
        event_name="osrs_item_deleted",
        message=f"Deleted item ID: {item_id}",
        request_id=req_id,
        item_id=item_id,
        deleted_by=current_user
    )

    return {
        "status": "success",
        "message": "Item successfully deleted"
    }


# @info: Delete endpoint for the OSRS database
# @param item_id - the 4 digit id 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.delete("/delete-all",
                summary="OSRS database Delete endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/5seconds") # Only 1 delete every 5 seconds
def osrs_database_delete(request: Request,
                         user: dict = Depends(require_admin)):
    
    req_id = getattr(request.state, "request_id", None)
    admin_user = user.get("username") or user.get("user")
    # clear the entire database
    delete_count = delete_all_items()

    # If the database was empty, throw an exception
    if delete_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database is already empty. No items were deleted."
            )

    log_event(
        level="WARNING",
        event_name="osrs_delete_all",
        message=f"Cleared OSRS database. {delete_count} items removed.",
        request_id=req_id,
        items_removed=delete_count,
        action_by=admin_user
    )

    return {
        "status": "success",
        "message": f"OSRS database cleared successfully. {delete_count} items removed.",
    }


# @info: Debug helper function to print the current 
#        OSRS database IDs
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.get("/ids",
            summary="OSRS database IDs endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("10/seconds") # This needs to be higher, so 10 every second
def osrs_database_registered_ids(request: Request,
                                 user: dict = Depends(require_auth)):
    # Get the current IDs
    all_current_ids = get_all_ids()

    # make sure it exists
    if not all_current_ids:
        raise HTTPException(status_code=404, detail="No IDs were found in OSRS database")
    
    return {
        "ids": all_current_ids
    }

# @info: Debug helper function to print the user
#        database content
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/database")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def print_database(user: dict = Depends(require_auth)):
    return print_database_info()

# Assignment 6 endpoint
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/health")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def health_status(user: dict = Depends(require_auth)):
    return {"status": "UP", "db": "UP"}

# Assignment 6 endpoint
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/health/live")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def health_status(user: dict = Depends(require_auth)):
    return {"status": "UP", "db": "UP"}

# Assignment 6 endpoint
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/health/ready")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def health_status(user: dict = Depends(require_auth)):
    return {"status": "UP", "db": "UP"}

#####################################################################


# Launch the backend server apon startup of the application
if __name__ == "__main__":
    #HOST = "127.0.0.1" # original
    HOST = "0.0.0.0"
    PORT = 8000

    # for docker
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(base_dir, "cert.pem")
    key_path = os.path.join(base_dir, "key.pem")

    uvicorn.run("main:app", 
                host=HOST, 
                port=PORT, 
                reload=False,# original = True
                ssl_certfile=cert_path,
                ssl_keyfile=key_path)

    # original
    # uvicorn.run("main:app", 
    #             host=HOST, 
    #             port=PORT, 
    #             reload=True,
    #             ssl_certfile="cert.pem",
    #             ssl_keyfile="key.pem")