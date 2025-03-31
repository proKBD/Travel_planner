# AI Travel Planner

An AI-powered travel planning system that helps users create personalized travel itineraries based on their preferences, budget, and travel dates.

## Features

- Interactive conversation to gather travel preferences
- Budget-aware recommendations
- Personalized day-by-day itinerary generation
- Consideration of dietary preferences and mobility concerns
- Activity suggestions based on user interests

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Google Gemini API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```
   You can get a free API key from: https://makersuite.google.com/app/apikey
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Start the application
2. Enter your travel preferences and requirements
3. The AI will guide you through the planning process
4. Get your personalized travel itinerary

## Environment Variables

- `GOOGLE_API_KEY`: Your Google Gemini API key for accessing the AI model

## Note

This application uses the free tier of Google's Gemini API, which has generous usage limits. No credit card required.

## Deployment

### Option 1: Deploy on Streamlit Cloud (Recommended)

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository, branch, and the `app.py` file
6. Add your environment variables:
   - Go to "Advanced settings"
   - Add `GOOGLE_API_KEY` with your Gemini API key
7. Click "Deploy"

### Option 2: Deploy on Heroku

1. Create a `Procfile` in your project root:
   ```
   web: streamlit run app.py
   ```

2. Create a `runtime.txt` file:
   ```
   python-3.9.18
   ```

3. Install the Heroku CLI and deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

4. Set your environment variables:
   ```bash
   heroku config:set GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Option 3: Deploy on Python Anywhere

1. Sign up for a Python Anywhere account
2. Upload your files to Python Anywhere
3. Create a new web app
4. Configure the web app to run your Streamlit app
5. Set your environment variables in the web app configuration
6. Reload your web app

### Important Deployment Notes

1. Make sure to keep your API key secure and never commit it to version control
2. Consider using environment variables for all sensitive information
3. Monitor your API usage to stay within free tier limits
4. Test your deployment thoroughly before making it public 