# API Documentation

## 3rd PArty API 

For this assignment, I integrated an item API for one of my favourite videogames Oldschool Runescape (OSRS). OSRS is a MAssively Multiplayer Online Role-PLaying Game (MMORPG), meaning it has a large playerbase that connect to persistent servers and play together. This genre of games often include virtual economies, where by, players can obtain items and sell them in a virutal marketplace in exchange for in-game currency. OSRS is, in my opintion, one of the best and largest examples of such an economy. As a result, the playerbase as created tools to track prices of all tradable items. 

I have integrated a simple item search endpoint for my API. Currently, it will send a get request to OSRS' servers to find information about a 'Rune Scimitar', a very common early game weapon. This get request returns all information abou this item including its descrition, item ID, currently traded value, and more. 

## OSRS database

I have created a new database to track OSRS items. This database can be interacted with directly by the user, assuming proper authentication and privilege. Using the application the user can create their own fake OSRS items and enter them into the database. I have also included an endpoint that returns all the registered item ID's that are currently tracked in the database. Once the item has been entered, the user can attempt to delete items by their ID. The create and delete endpoints require standard authentication, so that any authenticated user can interact with the database. I have also included a Delete all button, wiht an accompanying endpoint. This endpoints function is the wipe the entire OSRS database. Since this endpoint is so powerful, ans destructive, I have locked its use behind an additional level of security. It currently requires admin privlages. As such, when the user attempts to use it, it will return a '403' error becuase they do not have the correct privilege. 

This database is persistent, and it saved to the root directory. In the future, it may make more sense to have the database saved to the /backend direcotry to be next to the osrsdatabase code. This willbe implemented in the future.  

## CRUD operations

For the OSRS database, I have included basic CRUD operations. The Create, Read, Update, and delete operations have their own respective endpoint. All require standard authentication to use. I have also included a Delete-All endpoint. This endpoint is locked behind Admin privileges. Additonally, all the CRUD endpoints have been organized into their own osrs router gateway. This gateway is specific to the OSRS database. Each endpoint utilizes the standard REST methods. For Create a 'post' is used, Read uses 'get', update uses 'post', and delete utilizes 'delete'. Each endpoint also utilized simple error handling to make sure elements of the database are available before returning any false information back to the frontend.

## Rate Limiting
Where applicable I have also implemented rate limiting. The Rate limiting is designed to mitigate the kind of cyber attacks that would overload, and possibly crash, the application. When a user has exceeded the limited Rate, his or her request is rejected. Certain endpoint have different limiting rates. For the endpoint that modify data in the OSRS database, a lower rate is encoded. For endpoint that report data, a higher rate is allowed.

## Error Handling

For each endpoint, where applicable, i have implemented simple erorr handling to check for available data. For example, when attempting to delete element from the OSRS database, I check to make sure the ID exists before attempting to delete it from the database. Without this error checking, a serious error could occur. Additionally,  for the Read endpoint, I check to make sure it ID exists. Without this Error checking, an error or trash data could be sent to the user in the frontend.

## Authentication and Authorization

I have implemented OAuth2 authentication through GitHub login. This authentication stores the authentication token in the client side cookies. Wihtout this authentication the user cannot access the majority of the application's endpoints. Each endpoint first checks the authentication by using a authentication helper function i have created. This function is called 'require_auth'. In addition to the authentication, I have also implemented a 'role' field in the user database. This 'role' field stores the type of user that has been authenticated. A standard user will be able to utilize all endpoint that require standard authentication. However, I have also created a Delte-All endpoint for the OSRS database. This endpoint is specifically designed to be destructing to the OSRS database. As such, this endpoint is locked behind Administrative roles. 

## Containerization

I have containerized this project using Docker. I have personal experience with Docker at my job, so some of it was famailiar. However, there are certain aspects of this project that are very new to me. For example, I have not attempted to implement an https connection before, and I ran into trouble. Originally, I had the connection key and certification located in the root direcotry of the application. Docker would build successfully, but when I attempted to launch the program, I would run into rejected requests when trying to use my endpoints. The resolution to this problem was to move the key and certification into the backend in the same direcotry as the 'Dockerfile.backend'. I also ran into some trouble because of a messy project structure. Currently, my frontend fiels are sitting in the root directory. This is admittedly bad practice, and will soon be organized into a /frontend folder. This challenged showed up in my docker-compose.yml script. I ran into a few context issues in the build process, but this was solved relativly quickly.

The result of this containerization, is a more 'safe' build-process for this project. I am more confident that anyone can pull my code and build it successfully. The build process is also easier. Asside from the HTTPS certification generation, the build process only requires one command 'docker-compose build --no-cache'. The '--no-cache' assures that the user will not use any previous build attempt to be ccarried forward into a new build. As a side effect however, the application start command has changed. The old process required the user to use npm directly with 'npm run start-all'. Now the user must interface with the container and use 'docker-compose up' to start the container, and not the application directly.

