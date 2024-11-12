# Ollama Python Client

## Overview
Ollama Python Client is a Streamlit-based web application that allows users to interact with AI models using a chatbot interface. The application supports multiple sessions, and each session maintains its own conversation history. The chat history is stored in a SQLite database, enabling users to review and manage past interactions.

## Features
- **Multiple Sessions**: Create and manage multiple chat sessions with unique session names.
- **Persistent Conversations**: All conversation histories are saved to a SQLite database and can be reviewed anytime.
- **Model Selection**: Users can select from a list of available AI models to generate responses.

## Requirements
- Python 3.7+
- Streamlit
- SQLite3
- Requests
- Ollama installed and running (accessible via command line)

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/ollama-client.git
    cd ollama-client
    ```

2. **Create a Virtual Environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Ensure Ollama is Running**:
    Make sure Ollama is installed and accessible via the command line.

## Running the Application

To start the Streamlit app, run the following command:
```bash
streamlit run app.py
```
This will open the application in your default web browser.

## Usage

1. **Select an AI Model**: In the sidebar, select a model from the list of available models (these are fetched from Ollama).
2. **Create a New Session**: Provide a name for a new chat session and click "Create Session".
3. **Interact with the Model**: Enter your input in the text box and click "Send". The AI model will generate a response, which will be displayed in the chat interface.
4. **View Conversation History**: You can view past conversations in the "Conversation History" section.

## Database Schema
- **Session Table**: Stores session details (session ID, name, timestamp).
- **Conversations Table**: Stores conversation details for each session (session ID, model name, user input, bot response, timestamp).

## Project Structure
- `app.py`: Main application file containing the Streamlit interface and functionality.
- `chat_history.db`: SQLite database file storing the session and conversation data.
- `requirements.txt`: List of dependencies needed to run the application.

## Known Issues
- Ensure Ollama is installed and running correctly; otherwise, model information may not be retrieved successfully.
- Only local instances of Ollama are supported.

## Contributing
Feel free to open issues or submit pull requests. Contributions are welcome!

## License
This project is licensed under the MIT License.

## Acknowledgements
- **Streamlit**: For providing an easy and interactive way to build data applications.
- **Ollama**: For powering the model backend and providing AI model services.

## Contact
For questions or feedback, please open an issue in the repository or contact `your.email@example.com`.

