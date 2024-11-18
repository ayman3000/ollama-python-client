from gc import enable

import streamlit as st
import sqlite3
import subprocess
import requests
import json
import time
from datetime import datetime

# Global variable for database connection
conn = None

# Initialize database and create tables if they don't exist
def initialize_database():
    global conn
    if conn is None:
        conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    # Create the session table
    c.execute('''
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create the conversations table with response_time column
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            model_name TEXT,
            user_input TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES session(id)
        )
    ''')
    # Check if response_time column exists, and add it if not
    c.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in c.fetchall()]
    if 'response_time' not in columns:
        c.execute('ALTER TABLE conversations ADD COLUMN response_time REAL')
        conn.commit()
    else:
        conn.commit()
# Function to get a list of available models from the command line
def get_available_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        models = [line.split()[0] for line in lines[1:]]  # Skip the header line and get the model name
        return models
    except subprocess.CalledProcessError as e:
        st.error(f"Error retrieving model list: {e}")
        return []
    except FileNotFoundError:
        st.error("Ollama is not installed or not found in system PATH.")
        return []

# Function to generate a response from the selected model and measure response time
def generate_response(model_name, user_input):
    url = f'http://localhost:11434/api/generate'
    headers = {'Content-Type': 'application/json'}
    data = {
        'model': model_name,
        'prompt': user_input,
        'stream': False
    }
    start_time = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(data))
    end_time = time.time()
    response_time = end_time - start_time  # Calculate response time
    if response.status_code == 200:
        return response.json().get('response', ''), response_time
    else:
        error_message = response.json().get('error', 'Unknown error.')
        st.error(f"Error communicating with the model: {error_message}")
        return '', response_time

# Function to save conversation to the database, including response time
def save_conversation(session_id, model_name, user_input, bot_response, response_time):
    global conn
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (session_id, model_name, user_input, bot_response, response_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, model_name, user_input, bot_response, response_time))
    conn.commit()

# Function to create a new session and return its ID
def create_new_session(name):
    global conn
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO session (name)
            VALUES (?)
        ''', (name,))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        st.warning("Session name already exists. Please choose a different name.")
        return None

# Function to load all sessions
def load_sessions():
    global conn
    c = conn.cursor()
    c.execute('SELECT id, name FROM session ORDER BY timestamp DESC')
    return c.fetchall()

# Function to load conversation history by session ID, including response time
def load_conversation_history(session_id):
    global conn
    c = conn.cursor()
    c.execute('''
        SELECT user_input, bot_response, model_name, timestamp, response_time
        FROM conversations
        WHERE session_id = ?
        ORDER BY timestamp DESC
    ''', (session_id,))
    return c.fetchall()

# Function to delete a session by ID
def delete_session(session_id):
    global conn
    c = conn.cursor()
    c.execute('DELETE FROM conversations WHERE session_id = ?', (session_id,))
    c.execute('DELETE FROM session WHERE id = ?', (session_id,))
    conn.commit()

# Initialize the database
initialize_database()

# Set page layout to wide to utilize empty margins
st.set_page_config(page_title='ollama-client', layout="wide")

# Streamlit UI
st.title('Ollama Client')

# Sidebar for model selection and session list
st.sidebar.title('Select Model')
models = get_available_models()
if models:
    selected_model = st.sidebar.selectbox('Model', models)
else:
    st.sidebar.warning("No models found. Please check your Ollama installation.")

# Section for creating a new session
st.sidebar.subheader('Create New Session')

# Function to add a new session immediately after pressing Enter
def add_new_session():
    name = st.session_state.session_name
    if name:
        # Create a new session and store it in the session state
        session_id = create_new_session(name)
        if session_id:
            st.session_state['current_session_id'] = session_id
            st.session_state['current_session_name'] = name

            # Add the new session to the session list in memory without refreshing
            if 'session_list' not in st.session_state:
                st.session_state['session_list'] = []
            st.session_state['session_list'].insert(0, (session_id, name))

            # Clear the new session name input
            st.session_state['session_name'] = ""
            st.rerun()
        else:
            st.session_state['session_name'] = ""

new_session_name = st.sidebar.text_input("Enter new session name:", key='session_name', on_change=add_new_session)

# Sidebar list for existing sessions
st.sidebar.subheader('Session History')
if 'session_list' not in st.session_state:
    st.session_state['session_list'] = load_sessions()

# Create a list of session names for selection
session_names = [session_name for session_id, session_name in st.session_state['session_list']]

# Use a radio button to select a session
selected_session_name = st.sidebar.radio("Choose a session", session_names)

# Update the current session ID based on the selected session name
for session_id, session_name in st.session_state['session_list']:
    if session_name == selected_session_name:
        st.session_state['current_session_id'] = session_id
        st.session_state['current_session_name'] = session_name
        break

# Delete session button
if st.sidebar.button('Delete Selected Session'):
    if 'current_session_id' in st.session_state and st.session_state['current_session_id'] is not None:
        delete_session(st.session_state['current_session_id'])
        st.session_state['session_list'] = load_sessions()
        st.session_state['current_session_id'] = None
        st.session_state['current_session_name'] = None
        st.rerun()

# Retrieve the current session details
current_session_id = st.session_state.get('current_session_id')
current_session_name = st.session_state.get('current_session_name', 'Unnamed Session')

# Main chat interface
st.subheader(f'Chat - {current_session_name}')



user_input = st.text_area('You:', '',  key='user_input', placeholder='Write your message')

# send_prompt = False
# if st.session_state['enable_send'] == True and user_input and user_input.strip()!='' and current_session_id:

def send_message():
    if user_input and current_session_id:
        bot_response, response_time = generate_response(selected_model, user_input)

        if bot_response:
            save_conversation(current_session_id, selected_model, user_input, bot_response, response_time)
        else:
            st.warning('Please create or select a session.')
    else:
        st.toast('Please write your message first.')

st.button("Send", on_click=send_message)

# Search bar for filtering conversation history
search_query = st.text_input('Search Conversation History', '')

# Display the conversation history for the current session below the chat interface
if current_session_id:
    st.subheader(f'Conversation History - {current_session_name}')
    full_conversation = load_conversation_history(current_session_id)
    filtered_conversation = [
        conv for conv in full_conversation
        if search_query.lower() in conv[0].lower() or search_query.lower() in conv[1].lower()
    ]
    for user_msg, bot_msg, model_name, msg_timestamp, response_time in filtered_conversation:
        # Format the timestamp
        formatted_time = datetime.strptime(msg_timestamp, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %H:%M')

        formatted_response_time = f"{float(response_time):0.2f}" if response_time else ""
        st.markdown(
            f"<div style='text-align: left; background-color: #0056b3; color: white; padding: 10px; border-radius: 10px; margin: 5px 0;font-size:18px'>"
            f"<strong>You:</strong> {user_msg}"
            f"<span style='float: right; font-size: 14px; color: #e6e6e6;'>{formatted_time}</span></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align: left; background-color: #444; padding: 10px; border-radius: 10px; margin: 5px 0;font-size:18px'>"
            f"<strong style='color: #00b3b3;'>{model_name}:</strong>"
            f"<span style='float: right; font-size: 14px; color: yellow;'><strong>Response time:</strong> {formatted_response_time} seconds</span> "
            f"<pre style='white-space: pre-wrap; word-wrap: break-word; font-size:16px; background-color: #333; color: white !important; padding: 10px; border-radius: 5px;'>{bot_msg}</pre>"
            f"</div>",
            unsafe_allow_html=True)

# Custom CSS to remove the empty margins
st.markdown("""
    <style>
     .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 96%;
        margin: auto;
    }
    </style>
""", unsafe_allow_html=True)
