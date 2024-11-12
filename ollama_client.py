import streamlit as st
import sqlite3
import subprocess
import requests
import json
from datetime import datetime


# Initialize database and create tables if they don't exist
def initialize_database():
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
    # Create the conversations table
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
    conn.commit()
    conn.close()


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


# Function to generate a response from the selected model
def generate_response(model_name, user_input):
    url = f'http://localhost:11434/api/generate'
    headers = {'Content-Type': 'application/json'}
    data = {
        'model': model_name,
        'prompt': user_input,
        'stream': False
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json().get('response', '')
    else:
        st.error('Error communicating with the model.')
        return ''


# Function to save conversation to the database
def save_conversation(session_id, model_name, user_input, bot_response):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (session_id, model_name, user_input, bot_response)
        VALUES (?, ?, ?, ?)
    ''', (session_id, model_name, user_input, bot_response))
    conn.commit()
    conn.close()


# Function to create a new session and return its ID
def create_new_session(name):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO session (name)
        VALUES (?)
    ''', (name,))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id


# Function to load all sessions
def load_sessions():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM session ORDER BY timestamp DESC')
    sessions = c.fetchall()
    conn.close()
    return sessions


# Function to load conversation history by session ID
def load_conversation_history(session_id):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''
        SELECT user_input, bot_response, model_name
        FROM conversations
        WHERE session_id = ?
        ORDER BY timestamp DESC
    ''', (session_id,))
    conversation = c.fetchall()
    conn.close()
    return conversation


# Initialize the database
initialize_database()

# Streamlit UI
st.title('Ollama Client ')

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
        st.session_state['current_session_id'] = session_id
        st.session_state['current_session_name'] = name

        # Add the new session to the session list in memory without refreshing
        if 'session_list' not in st.session_state:
            st.session_state['session_list'] = []
        st.session_state['session_list'].insert(0, (session_id, name))

        # Clear the new session name input
        st.session_state['new_session_name'] = ""
new_session_name = st.sidebar.text_input("Enter new session name:", key='session_name', on_change= add_new_session)

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

# Retrieve the current session details
current_session_id = st.session_state.get('current_session_id')
current_session_name = st.session_state.get('current_session_name', 'Unnamed Session')

# Main chat interface
st.subheader(f'Chat - {current_session_name}')
user_input = st.text_area('You:', '', height=100)

if st.button('Send'):
    if user_input and current_session_id:
        bot_response = generate_response(selected_model, user_input)

        if bot_response:
            st.text_area(f'{selected_model}:', bot_response, height=200)
            save_conversation(current_session_id, selected_model, user_input, bot_response)
    else:
        st.warning('Please create or select a session.')

# Display the conversation history for the current session below the chat interface
if current_session_id:
    st.subheader(f'Conversation History - {current_session_name}')
    full_conversation = load_conversation_history(current_session_id)
    for user_msg, bot_msg, model_name in full_conversation:
        st.markdown(
            f"<div style='text-align: right; background-color: #0056b3; color: white; padding: 10px; border-radius: 10px; margin: 5px 0;font-size:18px'><strong>You:</strong> {user_msg}</div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align: left; background-color: #333333; color: white; padding: 10px; border-radius: 10px; margin: 5px 0;font-size:18px'><strong style='color:#00b3b3;font-size:20px'> {model_name}:</strong> <pre style='white-space: pre-wrap; word-wrap: break-word; font-size:16px; background-color: #2e2e2e; color: #d4d4d4; padding: 10px; border-radius: 5px;'>{bot_msg}</pre></div>",
            unsafe_allow_html=True)

# Custom CSS for font sizes
st.markdown("""
    <style>
    /* Title Font Size */
    h1 {
        font-size: 24px !important;
        margin-top:-60px;
    }
    /* Subheader Font Size */
    h2 {
        font-size: 18px !important;
    }
    /* Sidebar Font Size */
    .css-18e3th9, .css-1d391kg {
        font-size: 14px !important;
    }
    /* Input box and button text */
    input, button {
        font-size: 16px !important;
    }
    p {
        font-size: 18px !important;
    }
    /* Conversation History Text */
    .stMarkdown {
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Custom CSS to remove the extra top margin
st.markdown("""
    <style>
    /* Remove padding above the title */
    .css-18e3th9 {
        padding-top: 0rem;
    }
    </style>
""", unsafe_allow_html=True)