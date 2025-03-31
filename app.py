import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import time

def initialize_gemini():
    """Initialize and test Gemini API connection"""
    try:
        # Load and configure API key
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            st.error("API key not found. Please check your .env file.")
            return False

        genai.configure(api_key=api_key)
        
        # Use Gemini 2.0 Flash model (free tier)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Test the connection with a simple prompt
        try:
            response = model.generate_content("Hi")
            if response and response.text:
                st.success("Successfully connected to Gemini API!")
                return model
            else:
                st.error("Could not get a valid response from Gemini API.")
                return False
        except Exception as api_error:
            st.error(f"Error testing Gemini API connection: {str(api_error)}")
            return False
            
    except Exception as e:
        st.error(f"Error configuring Gemini API: {str(e)}")
        return False

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
if 'asked_questions' not in st.session_state:
    st.session_state.asked_questions = set()

def get_ai_response(prompt):
    """Get response from Gemini API"""
    try:
        # Get model from session state
        if 'model' not in st.session_state:
            st.error("Model not initialized")
            return None
            
        model = st.session_state.model
        print(f"Sending prompt to Gemini: {prompt[:100]}...")  # Debug log
        
        # Generate response with retry logic
        for _ in range(3):  # Try up to 3 times
            try:
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as retry_error:
                print(f"Retry error: {str(retry_error)}")
                time.sleep(1)  # Wait 1 second before retrying
                continue
                
        st.error("Failed to get response from Gemini API after multiple attempts")
        return None
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        print(f"Detailed error: {str(e)}")  # Debug log
        return None

def extract_preferences(user_input):
    """Extract user preferences from input"""
    prompt = f"""As a travel planning assistant, analyze this input and extract travel preferences.
    Return a detailed JSON object with:
    - budget (exact amount or level: budget-friendly/mid-range/luxury)
    - duration (number of days)
    - destination (specific place)
    - starting_location (departure city/place)
    - purpose (main goal: relaxation/adventure/culture/etc)
    - preferences (list of specific activities/interests mentioned)
    - dietary_restrictions (any food preferences/restrictions)
    - mobility_concerns (any physical considerations)
    - accommodation_preferences (preferred stay type)
    
    Consider context and implied preferences.
    Set fields to null if not mentioned.
    For lists, return null if empty.
    
    User input: {user_input}
    
    Return only the JSON object."""
    
    response = get_ai_response(prompt)
    if response:
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            prefs = json.loads(response)
            # Convert empty lists to None
            for key in ['preferences', 'dietary_restrictions']:
                if key in prefs and (not prefs[key] or prefs[key] == []):
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
        'budget': "I'd love to help you plan a rejuvenating trip! Could you tell me your budget? (e.g., budget-friendly, mid-range, luxury, or a specific amount)",
        'duration': "Perfect! How long would you like to take for this journey? Take your time to decide - it's important to give yourself enough space to unwind.",
        'destination': "Is there a particular place you've been dreaming of visiting? I can suggest some peaceful and beautiful destinations if you'd like.",
        'starting_location': "Where will you be starting your journey from?",
        'purpose': "What's the main purpose of your trip? Are you looking for adventure, relaxation, or something specific?",
        'preferences': "What kinds of activities interest you most? (e.g., nature walks, adventure sports, sightseeing, local experiences)",
        'dietary_restrictions': "Do you have any dietary preferences or restrictions I should keep in mind?",
        'mobility_concerns': "Do you have any mobility concerns I should consider while planning?",
        'accommodation_preferences': "What type of accommodation would you prefer? (e.g., hotel, guesthouse, hostel)"
    }
    
    # Priority order for questions
    priority_fields = ['budget', 'duration', 'destination', 'starting_location', 'purpose', 'preferences', 
                      'accommodation_preferences', 'dietary_restrictions', 'mobility_concerns']
    
    # Get the first missing field by priority that hasn't been asked yet
    for field in priority_fields:
        if field in missing_fields and field not in st.session_state.asked_questions:
            st.session_state.asked_questions.add(field)
            return questions.get(field)
    
    return None

def generate_itinerary(preferences):
    """Generate a detailed travel itinerary based on preferences"""
    # Create a dynamic prompt based on user preferences
    prompt = f"""Create a personalized {preferences['duration']}-day trip itinerary.

    Trip Details:
    - Destination: {preferences['destination']}
    - Starting Location: {preferences['starting_location']}
    - Budget Level: {preferences['budget']}
    - Trip Purpose: {preferences['purpose']}
    - Accommodation Type: {preferences['accommodation_preferences']}
    {f"- Dietary Needs: {preferences['dietary_restrictions']}" if preferences.get('dietary_restrictions') else ""}
    {f"- Mobility Considerations: {preferences['mobility_concerns']}" if preferences.get('mobility_concerns') else ""}
    {f"- Activity Preferences: {preferences['preferences']}" if preferences.get('preferences') else ""}

    Please provide:
    1. Travel Plan:
       - Best route from {preferences['starting_location']} to {preferences['destination']}
       - Transportation options and estimated travel time
       - Recommended stops along the way

    2. Day-by-Day Itinerary:
       - Day 1: Detailed travel and arrival plan
       - Days 2-{preferences['duration']}: Daily activities tailored to {preferences['purpose']}
       - Flexible timing for activities

    3. Accommodation:
       - Current available hotels/stays matching {preferences['budget']} budget
       - Location recommendations based on planned activities

    4. Local Experiences:
       - Current seasonal activities in {preferences['destination']}
       - Local food specialties and recommended restaurants
       - Cultural events or festivals if happening now

    5. Practical Information:
       - Weather-appropriate activity suggestions
       - Current local transportation options
       - Estimated daily costs based on chosen activities
       - Local emergency contacts and medical facilities

    Format the response in a clear, day-by-day structure.
    Focus on real-time recommendations and current local conditions.
    Include alternative options for flexibility."""
    
    try:
        response = get_ai_response(prompt)
        if response:
            return response
        else:
            return "I apologize, but I couldn't generate the itinerary. Please try again."
    except Exception as e:
        print(f"Error generating itinerary: {str(e)}")
        return "Sorry, there was an error generating your itinerary. Please try again."

def main():
    st.title("AI Travel Planner")
    
    # Initialize Gemini at the start
    if 'model' not in st.session_state:
        model = initialize_gemini()
        if not model:
            st.stop()
        st.session_state.model = model

    st.write("Hi there! 👋 I'm your friendly AI travel assistant. I'm here to help you plan a wonderful and rejuvenating trip. Let's create an experience that brings you joy and peace.")

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
        
        # Check if user wants itinerary
        if any(word in user_input.lower() for word in ["itinerary", "plan", "create", "generate", "show"]):
            if all(st.session_state.user_preferences[k] is not None for k in ['budget', 'duration', 'destination', 'starting_location']):
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "I'll create your itinerary now..."
                })
                itinerary = generate_itinerary(st.session_state.user_preferences)
                if itinerary:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Here's your personalized itinerary for {st.session_state.user_preferences['destination']}:\n\n{itinerary}"
                    })
            else:
                missing = [k.replace('_', ' ').title() for k in ['budget', 'duration', 'destination', 'starting_location'] 
                          if st.session_state.user_preferences[k] is None]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"I still need some essential information before I can create your itinerary: {', '.join(missing)}"
                })
        else:
            # Extract preferences from user input
            extracted_prefs = extract_preferences(user_input)
            if extracted_prefs:
                # Update user preferences
                for key, value in extracted_prefs.items():
                    if value is not None:
                        st.session_state.user_preferences[key] = value
            
            # Get next question based on missing information
            next_question = get_next_question(st.session_state.user_preferences)
            
            if next_question:
                st.session_state.chat_history.append({"role": "assistant", "content": next_question})
            elif all(v is not None for v in [st.session_state.user_preferences[k] for k in ['budget', 'duration', 'destination', 'starting_location']]):
                destination = st.session_state.user_preferences['destination']
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"Great! I have all the essential information about your trip to {destination}. Type 'create itinerary' and I'll generate a detailed plan for you."
                })
        
        st.rerun()

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
    if all(v is not None for v in [st.session_state.user_preferences[k] for k in ['budget', 'duration', 'destination', 'starting_location']]):
        if st.button("Generate Travel Itinerary"):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I'll create your itinerary now..."
            })
            itinerary = generate_itinerary(st.session_state.user_preferences)
            if itinerary:
                st.subheader("Your Personalized Travel Itinerary")
                st.write(itinerary)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Here's your personalized itinerary for {st.session_state.user_preferences['destination']}:\n\n{itinerary}"
                })

if __name__ == "__main__":
    main() 