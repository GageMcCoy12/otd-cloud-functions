import json
import os
import time
from typing import Dict, List, Any
import requests

def main(context):
    # Simple debug output
    print("StyleBot function started")
    
    # Get OpenAI API key from environment variables
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("ERROR: OpenAI API key not found in environment variables")
        return context.res.json({
            'success': False,
            'error': "StyleBot is not properly configured. Please contact support."
        }, 500)
    
    # Get the request data
    request_data = context.req.body
    print(f"Raw request data: {request_data}")
    
    # Parse the JSON string if it's a string
    if isinstance(request_data, str):
        try:
            request_data = json.loads(request_data)
            print(f"Parsed request data: {request_data}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return context.res.json({
                'success': False,
                'error': f'Error parsing JSON request: {str(e)}'
            }, 400)
    
    try:
        # Extract data from payload
        message = request_data.get('message', '')
        conversation_history = request_data.get('conversation_history', [])
        user_style_preferences = request_data.get('user_style_preferences', {})
        selected_stylebot = request_data.get('selected_stylebot', 'lexi')
        
        # If we couldn't extract a message, return an error
        if not message:
            print("No message found in request")
            return context.res.json({
                'success': False,
                'error': "Message is required"
            }, 400)
        
        print(f"Processing message: {message}")
        print(f"Selected StyleBot: {selected_stylebot}")
        
        # Format conversation history for OpenAI
        formatted_history = []
        for msg in conversation_history:
            if isinstance(msg, dict):
                formatted_history.append({
                    "role": "user" if msg.get("isUser") else "assistant",
                    "content": msg.get("text", "")
                })
        
        # Get stylist personality based on selected StyleBot
        stylist_personality = get_stylebot_personality(selected_stylebot)
        
        # Create system prompt with user preferences and stylist personality
        system_prompt = create_system_prompt(user_style_preferences, stylist_personality)
        
        # Prepare messages array for OpenAI
        messages = [
            {"role": "system", "content": system_prompt},
            *formatted_history,
            {"role": "user", "content": message}
        ]
        
        print("Calling OpenAI API...")
        
        # Call OpenAI API
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.95
            }
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Extract AI response
        ai_message = response_data['choices'][0]['message']['content']
        
        print(f"AI response received: {ai_message[:50]}...")
        
        # Return response to client
        return context.res.json({
            'success': True,
            'response': {
                'message': ai_message,
                'conversation_id': str(int(time.time()))
            }
        })
        
    except Exception as e:
        print(f"Error processing StyleBot request: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return context.res.json({
            'success': False,
            'error': "Sorry, StyleBot is having trouble right now. Please try again in a moment."
        }, 500)

def create_system_prompt(user_preferences: Dict, stylist_personality: str) -> str:
    prompt = f"{stylist_personality}\n\n"
    prompt += "Your goal is to provide engaging, personalized style advice in a friendly and casual tone using plain text and emojis. "
    prompt += "Keep your responses short and conversational, and avoid any markdown formatting like asterisks or bold text. "
    prompt += "If you don't have enough details about the user's vibe or wardrobe, ask clarifying questions first. "
    prompt += "Only finalize an outfit plan when you're confident you have all the necessary details.\n\n"
    
    if user_preferences.get("aesthetics"):
        prompt += "User's aesthetic preferences: " + ", ".join(user_preferences['aesthetics']) + ". "
    if user_preferences.get("brands"):
        prompt += "Favorite brands: " + ", ".join(user_preferences['brands']) + ". "
    if user_preferences.get("keyPieces"):
        prompt += "Wardrobe key pieces: " + ", ".join(user_preferences['keyPieces']) + ". "
    if user_preferences.get("styleGoal"):
        prompt += "Style goal: " + user_preferences['styleGoal'] + ". "
    
    prompt += "\n\nGuidelines:\n"
    prompt += "- Ask clarifying questions if the user's vibe or available clothing details are unclear 😊\n"
    prompt += "- Keep your messages short, plain, and conversational 😊\n"
    prompt += "- Avoid markdown formatting; use plain text and emojis only 😊\n"
    prompt += "- Provide specific and actionable styling suggestions once you have enough info\n"
    prompt += "- Encourage the user and be supportive in your advice 😊"
    
    return prompt

def get_stylebot_personality(stylebot_id: str) -> str:
    personalities = {
        'lexi': "You are Lexi, a cheerful and candid fashion assistant. Your tone is upbeat and friendly, with a dash of playfulness. You're knowledgeable about current trends but also appreciate timeless pieces. You speak like a supportive friend who's excited to help style outfits.",
        'stella': "You are Stella, a trendy fashion assistant who stays on the cutting edge. Your tone is cool and confident, with an eye for the latest styles. You love experimenting with fashion and encourage users to step out of their comfort zone, while still respecting their personal style.",
        'vivi': "You are Vivi, a confident and fashion-forward assistant. Your tone is sophisticated and polished, with authoritative style knowledge. You focus on creating cohesive, well-put-together looks that make a statement, and you value quality over quantity.",
        'bella': "You are Bella, an energetic and upbeat fashion assistant. Your tone is enthusiastic and encouraging, making styling fun and accessible. You're great at mixing high and low pieces and finding budget-friendly alternatives to trending styles."
    }
    return personalities.get(stylebot_id, personalities['lexi'])
