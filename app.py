import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set your GOOGLE_API_KEY in the .env file")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
except Exception as e:
    st.error(f"Error configuring Gemini API: {str(e)}")
    st.stop()

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'context' not in st.session_state:
    st.session_state.context = """You are a friendly and knowledgeable travel guide assistant. Your role is to:
    1. Help users plan their trips
    2. Provide travel recommendations
    3. Share interesting facts about destinations
    4. Give practical travel tips
    5. Help with travel-related queries
    
    Important guidelines:
    - Keep responses concise and engaging
    - Don't repeat the same questions if the user hasn't answered them
    - If the user mentions a destination, ask about their preferences and budget in a single message
    - Share interesting facts about destinations when relevant
    - Maintain a friendly, conversational tone
    - If the user keeps saying the same thing (like "goa"), acknowledge it and move forward with planning
    - Don't ask too many questions at once - focus on 1-2 key details at a time"""
if 'last_input' not in st.session_state:
    st.session_state.last_input = None

def get_ai_response(user_input):
    """Get response from Gemini API"""
    try:
        # Create a prompt that includes context and conversation history
        prompt = f"""Context: {st.session_state.context}

Previous conversation:
{format_chat_history()}

User: {user_input}

Assistant:"""
        
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
        else:
            st.error("Empty response from Gemini API")
            return None
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return None

def format_chat_history():
    """Format the chat history for the prompt"""
    formatted_history = ""
    for message in st.session_state.chat_history:
        formatted_history += f"{message['role']}: {message['content']}\n"
    return formatted_history

def main():
    st.title("AI Travel Guide")
    st.write("Hi there! 👋 I'm your friendly AI travel guide. I can help you plan trips, recommend destinations, and share travel tips. What would you like to know about?")

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        else:
            st.write(f"Assistant: {message['content']}")

    # User input
    user_input = st.text_input("Ask me anything about travel:", key="user_input")
    
    if user_input and user_input != st.session_state.last_input:
        # Update last input
        st.session_state.last_input = user_input
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Get AI response
        ai_response = get_ai_response(user_input)
        if ai_response:
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            st.experimental_rerun()

if __name__ == "__main__":
    main() 