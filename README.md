# CS4390_ServerChat README
## How To Run The Application
### Requirements
All the needed dependencies and required modules  are listed in the requirement.txt file and can be installed by using the following command

Run “pip  install -r requirements.txt” to download all the needed libraries

Run “python db.py” to set up the database

### Downloading The Application
<ul>
<li>git clone https://github.com/emWojo/CS4390_ServerChat.git
<li>From E-Learning
  <ul>
<li>Download the project archive file ‘project-code.zip’ and extract the project folder from it.
  </ul>
</ul>

### Run Commands 

#### Server
To run the server-side portion of the application in the console

Type ‘’python serverMain.py

#### Client
To run the client side portion of the application in the console

Type ‘python Client_[Client_Name_Number].py’

For testing there are 4 Client_Name_Number number

Client_One.py, Client_Two.py, Client_Three.py, Client_Four.py

#### Clients Chats Commands
<ul>
<li>logon - Connect the client to the server </li>
<li>logoff - Disconnect the the client to the server </li>
<li>chat Target-Client-ID - Allows a client to send a chat request to the server </li>
<li>end chat  - Allows a client to send an end chat request to the server </li>
<li>end client - Closes the client chat application </li>
<li>end server - Closes the server application </li>
<li>history Target-Client-ID - Allows a client to see their chat history with another client. </li>
</ul>

## Chat Session Validation

### Basic Chat initiated and closed by A

### Basic Chat initiated by A , but B initially not connected

### Basic Chat initiated by C, but B is already in another chat  

### History Recall

### Simultaneous Chat Sessions
