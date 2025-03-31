import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

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
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'budget': None,
        'duration': None,
        'destination': None,
        'starting_location': None,
        'purpose': None,
        'preferences': [],
        'dietary_restrictions': [],
        'mobility_concerns': None,
        'accommodation_preferences': None
    }
if 'last_input' not in st.session_state:
    st.session_state.last_input = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'initial'
if 'asked_questions' not in st.session_state:
    st.session_state.asked_questions = set()

def get_ai_response(prompt):
    """Get response from Gemini API"""
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
        else:
            st.error("Empty response from Gemini API")
            return None
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return None

def extract_preferences(user_input):
    """Extract user preferences from input"""
    prompt = f"""You are a travel planning assistant. Extract key travel preferences from the user's input.
    Return a JSON object with these fields:
    - budget (if mentioned)
    - duration (if mentioned)
    - destination (if mentioned)
    - starting_location (if mentioned)
    - purpose (if mentioned)
    - preferences (list of interests/activities mentioned)
    - dietary_restrictions (if mentioned)
    - mobility_concerns (if mentioned)
    - accommodation_preferences (if mentioned)
    
    If a field is not mentioned, set it to null.
    For lists (preferences, dietary_restrictions), return null if empty.
    
    User input: {user_input}
    
    Return only the JSON object, no additional text."""
    
    response = get_ai_response(prompt)
    if response:
        try:
            # Clean the response to ensure it's valid JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            prefs = json.loads(response)
            # Convert empty lists to None
            for key in ['preferences', 'dietary_restrictions']:
                if key in prefs and prefs[key] == []:
                    prefs[key] = None
            return prefs
        except Exception as e:
            print(f"Error parsing JSON response: {str(e)}")
            return None
    return None

def get_next_question(preferences):
    """Get the next question to ask based on missing information"""
    missing_fields = [k for k, v in preferences.items() if v is None]
    if not missing_fields:
        return None
    
    # Create a mapping of fields to conversational questions
    questions = {
        'budget': "I'd love to help you plan your trip! Could you tell me your budget? (e.g., budget-friendly, mid-range, luxury, or a specific amount)",
        'duration': "That sounds great! How long would you like to stay there? (e.g., a weekend, a week, two weeks?)",
        'destination': "Great! Where would you like to go?",
        'starting_location': "Nice choice! Where will you be starting your journey from?",
        'purpose': "Interesting! What's the main reason for your trip? (e.g., relaxation, adventure, exploring culture, partying?)",
        'preferences': "I'm curious - what kind of activities interest you? (e.g., water sports, historical sites, yoga, nightlife, shopping, etc.)",
        'dietary_restrictions': "Before we plan your meals, do you have any dietary preferences or restrictions? (e.g., vegetarian, vegan, allergies)",
        'mobility_concerns': "Just to make sure I plan everything perfectly, do you have any mobility concerns I should be aware of?",
        'accommodation_preferences': "Last but not least, what kind of accommodation would you prefer? (e.g., hotel, resort, guesthouse, budget hostel)"
    }
    
    # Get the first missing field that hasn't been asked yet
    for field in missing_fields:
        if field not in st.session_state.asked_questions:
            st.session_state.asked_questions.add(field)
            return questions.get(field, f"Could you tell me about your {field.replace('_', ' ')}?")
    
    return None

def generate_itinerary(preferences):
    """Generate a detailed travel itinerary based on preferences"""
    prompt = f"""You are a travel planning expert. Generate a detailed day-by-day itinerary based on these preferences: {json.dumps(preferences)}
    
    Include:
    1. Daily schedule with timing
    2. Recommended activities and attractions
    3. Estimated costs
    4. Travel tips and considerations
    5. Local recommendations for food and accommodation
    
    Format the response in a clear, structured way with:
    - Day-by-day breakdown
    - Time slots for activities
    - Cost estimates
    - Travel tips
    - Local recommendations
    
    Make it personalized based on the user's preferences and constraints."""
    
    return get_ai_response(prompt)

def main():
    st.title("AI Travel Planner")
    st.write("Hi there! 👋 I'm your friendly AI travel assistant. I'll help you plan your perfect trip! Just tell me where you want to go, and I'll guide you through the planning process.")

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        else:
            st.write(f"Assistant: {message['content']}")

    # User input
    user_input = st.text_input("Tell me about your travel plans:", key="user_input")
    
    if user_input and user_input != st.session_state.last_input:
        # Update last input
        st.session_state.last_input = user_input
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Extract preferences from user input
        extracted_prefs = extract_preferences(user_input)
        if extracted_prefs:
            # Update user preferences
            for key, value in extracted_prefs.items():
                if value is not None:
                    st.session_state.user_preferences[key] = value
                    # Reset asked questions if destination changes
                    if key == 'destination':
                        st.session_state.asked_questions = set()

        # Get next question based on missing information
        next_question = get_next_question(st.session_state.user_preferences)
        
        if next_question:
            st.session_state.chat_history.append({"role": "assistant", "content": next_question})
        elif all(st.session_state.user_preferences.values()):
            destination = st.session_state.user_preferences['destination']
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"Perfect! I have all the information I need to create your perfect trip to {destination}. Would you like me to generate a detailed itinerary for you?"
            })
        
        st.experimental_rerun()

    # Display current preferences
    if any(st.session_state.user_preferences.values()):
        st.subheader("Your Travel Preferences")
        for key, value in st.session_state.user_preferences.items():
            if value is not None:
                if isinstance(value, list) and value:  # Only show non-empty lists
                    st.write(f"{key.replace('_', ' ').title()}: {', '.join(value)}")
                elif not isinstance(value, list):  # Show non-list values
                    st.write(f"{key.replace('_', ' ').title()}: {value}")

    # Generate itinerary button
    if all(st.session_state.user_preferences.values()):
        if st.button("Generate Travel Itinerary"):
            itinerary = generate_itinerary(st.session_state.user_preferences)
            if itinerary:
                st.subheader("Your Personalized Travel Itinerary")
                st.write(itinerary)

if __name__ == "__main__":
    main() 