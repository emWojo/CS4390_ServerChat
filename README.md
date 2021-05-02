# CS4390_ServerChat README
## How To Run The Application
### Requirements
All the needed dependencies and required modules  are listed in the requirement.txt file and can be installed by using the following command

Run `pip3  install -r requirements.txt` to download all the needed libraries

Run `python3 db.py` to set up the database

### Downloading The Application
- `git clone https://github.com/emWojo/CS4390_ServerChat.git`
- From E-Learning
   - Download the project archive file ‘project-code.zip’ and extract the project folder from it.


### Run Commands 

#### Server
To run the server-side portion of the application in the console

Type `python3 serverMain.py`

#### Client
To run the client side portion of the application in the console

Type `python3 Client_[Client_Name_Number].py`

For testing there are 4 Client_Name_Number number

Client_One.py, Client_Two.py, Client_Three.py, Client_Four.py

#### Clients Chats Commands
- `logon` - Connect the client to the server
- `logoff` - Disconnect the the client to the server
- `chat <Target-Client-ID>` - Allows a client to send a chat request to the server
   - <Target-Client-ID> is the id of the client, One -> 111, Two -> 222 and so on.
- `end chat`  - Allows a client to send an end chat request to the server
- `end client` - Closes the client chat application
- `end server` - Closes the server application
- `history <Target-Client-ID>` - Allows a client to see their chat history with another client.

## Chat Session Validation

### Basic Chat initiated and closed by A
![1](https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/initCloseA.gif)

### Basic Chat initiated by A and closed by B
![2](https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/initAendB.gif)

### Basic Chat initiated by A , but B initially not connected
![3](https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/initAnotConB.gif)

### Basic Chat initiated by C, but B is already in another chat
![4](https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/3interrupts.gif)

### History Recall
![5](https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/historyAB.gif)

### Simultaneous Chat Sessions
https://github.com/emWojo/CS4390_ServerChat/blob/main/gifs/5chats_v2.gif 
