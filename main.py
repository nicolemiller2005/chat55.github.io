from flask import Flask, render_template_string, request, redirect, url_for
from flask_socketio import SocketIO, emit
import socket

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Store clients
clients = {}

# HTML for the chat app
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>Chat App</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f4f4f9; }
        #login-container, #chat-container { width: 90%; max-width: 600px; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); overflow: hidden; }
        #login-container { padding: 20px; text-align: center; }
        #chat-box { height: 400px; overflow-y: scroll; padding: 10px; border-bottom: 1px solid #ccc; background-color: #fafafa; }
        #chat-box .message { margin: 8px 0; padding: 8px 12px; border-radius: 6px; max-width: 80%; }
        #chat-box .user-message { background-color: #007bff; color: #fff; margin-left: auto; text-align: right; }
        #chat-box .other-message { background-color: #e9e9eb; color: #333; }
        #chat-box .image-message img { max-width: 100%; border-radius: 6px; }
        #input-container { display: flex; padding: 10px; background-color: #fff; }
        #message { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin-right: 10px; }
        #send-btn, #send-image-btn { background-color: #007bff; color: #fff; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        #send-btn:hover, #send-image-btn:hover { background-color: #0056b3; }
        #file-input { display: none; }
        #admin-container { text-align: center; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js"></script>
</head>
<body>

<div id="login-container">
    <h2>Welcome to the Chat</h2>
    <input type="text" id="username" placeholder="Enter your name" required>
    <button id="start-chat-btn">Start Chatting</button>
</div>

<div id="chat-container" style="display: none;">
    <h2 style="text-align: center; margin-top: 10px;">Real-Time Chat</h2>
    <div id="chat-box"></div>
    <div id="input-container">
        <input type="text" id="message" placeholder="Type a message" autofocus>
        <button id="send-btn">Send</button>
        <button id="send-image-btn">📷</button>
        <input type="file" id="file-input" accept="image/*">
    </div>
</div>

<!-- Admin Page -->
<div id="admin-container" style="display: none;">
    <h2>Admin Panel</h2>
    <h3>Connected Users</h3>
    <ul id="user-list"></ul>
    <button id="logout-btn">Logout</button>
</div>

<script>
    const socket = io();
    let username;

    // Admin login logic
    const adminUsername = "admin";
    const adminPassword = "admin";
    let isAdmin = false;

    function showChat() {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('chat-container').style.display = 'block';
        socket.emit('new_user', username);
    }

    function showAdminPanel() {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('admin-container').style.display = 'block';
        // Update the user list for admin
        updateUserList();
    }

    // Handle admin login form
    function adminLogin() {
        const adminUsernameInput = prompt("Enter admin username:");
        const adminPasswordInput = prompt("Enter admin password:");
        if (adminUsernameInput === adminUsername && adminPasswordInput === adminPassword) {
            isAdmin = true;
            showAdminPanel();
        } else {
            alert("Incorrect credentials");
        }
    }

    document.getElementById('start-chat-btn').addEventListener('click', () => {
        const input = document.getElementById('username');
        username = input.value.trim();
        if (username) {
            if (username.toLowerCase() === adminUsername) {
                adminLogin();
            } else {
                showChat();
            }
        } else {
            alert("Please enter a name to start chatting.");
        }
    });

    function addMessage(content, isUser = false, isImage = false) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message ' + (isUser ? 'user-message' : 'other-message');
        
        if (isImage) {
            const img = document.createElement('img');
            img.src = content;
            messageElement.classList.add("image-message");
            messageElement.appendChild(img);
        } else {
            messageElement.textContent = content;
        }
        
        document.getElementById('chat-box').appendChild(messageElement);
        document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight;
    }

    socket.on('message', (data) => {
        const isUser = data.user === username;
        if (data.type === 'image') {
            addMessage(data.message, isUser, true);
        } else {
            addMessage(`${data.user}: ${data.message}`, isUser);
        }
    });

    document.getElementById('send-btn').addEventListener('click', () => {
        const messageInput = document.getElementById('message');
        const message = messageInput.value;
        if (message.trim()) {
            socket.emit('message', { user: username, message: message, type: 'text' });
            messageInput.value = '';
        }
    });

    document.getElementById('send-image-btn').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });

    document.getElementById('file-input').addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file && file.size < 1024 * 1024) {  // Limit to 1MB for performance
            const reader = new FileReader();
            reader.onload = function(e) {
                const base64Image = e.target.result;
                socket.emit('message', { user: username, message: base64Image, type: 'image' });
            };
            reader.readAsDataURL(file);
        } else {
            alert("File too large. Please select an image smaller than 1MB.");
        }
        // Clear file input for next upload
        document.getElementById('file-input').value = "";
    });

    document.getElementById('message').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('send-btn').click();
        }
    });

    // Admin Logout
    document.getElementById('logout-btn').addEventListener('click', () => {
        isAdmin = false;
        document.getElementById('admin-container').style.display = 'none';
        document.getElementById('login-container').style.display = 'block';
    });

    // Update user list for admin
    function updateUserList() {
        const userList = document.getElementById('user-list');
        userList.innerHTML = "";
        for (const clientId in clients) {
            const client = clients[clientId];
            const li = document.createElement('li');
            li.textContent = client.username;
            userList.appendChild(li);
        }
    }
</script>

</body>
</html>
"""

@app.route('/')
def chat():
    return render_template_string(html)

@socketio.on('connect')
def handle_connect():
    clients[request.sid] = {"ip": request.remote_addr, "username": None}
    print(f"{request.remote_addr} connected.")

@socketio.on('disconnect')
def handle_disconnect():
    username = clients.get(request.sid, {}).get("username", "A user")
    print(f"{username} disconnected.")
    emit("message", {"user": "System", "message": f"{username} has left the chat."}, broadcast=True)
    clients.pop(request.sid, None)

@socketio.on('new_user')
def handle_new_user(name):
    clients[request.sid]["username"] = name
    emit("message", {"user": "System", "message": f"{name} has joined the chat!"}, broadcast=True)

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

def find_free_port(starting_port=5000):
    port = starting_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

if __name__ == '__main__':
    port = find_free_port(5000)
    print(f"Starting server on port {port}...")
    socketio.run(app, host='0.0.0.0', port=port)
