import json
import os
import time
from typing import Dict, List, Any
import requests

def main(req, res):
    # Print raw request data without assuming format
    print("==== RAW REQUEST DATA ====")
    print(f"Request object type: {type(req)}")
    print(f"Request object dir: {dir(req)}")
    
    # Print all attributes of the request object
    for attr in dir(req):
        if not attr.startswith('__'):
            try:
                value = getattr(req, attr)
                if not callable(value):
                    print(f"req.{attr} = {repr(value)}")
            except Exception as e:
                print(f"Error accessing req.{attr}: {e}")
    
    # Try to access common attributes that might contain the payload
    print("\n==== POTENTIAL PAYLOAD LOCATIONS ====")
    
    # Check for raw body/payload
    if hasattr(req, 'body'):
        print(f"Raw req.body: {repr(req.body)}")
    
    if hasattr(req, 'payload'):
        print(f"Raw req.payload: {repr(req.payload)}")
    
    if hasattr(req, 'data'):
        print(f"Raw req.data: {repr(req.data)}")
    
    if hasattr(req, 'raw'):
        print(f"Raw req.raw: {repr(req.raw)}")
    
    if hasattr(req, 'content'):
        print(f"Raw req.content: {repr(req.content)}")
    
    if hasattr(req, 'text'):
        print(f"Raw req.text: {repr(req.text)}")
    
    print("====================================")
    
    # Get OpenAI API key from environment variables
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    if not openai_api_key:
        return res.json({
            "error": "StyleBot is not properly configured. Please contact support."
        }, 500)
    
    try:
        # Try to extract the payload without assuming format
        payload = None
        message = None
        conversation_history = []
        user_style_preferences = {}
        selected_stylebot = 'lexi'
        
        # Method 1: Try req.body
        if hasattr(req, 'body'):
            try:
                if isinstance(req.body, dict):
                    payload = req.body
                elif isinstance(req.body, str):
                    payload = json.loads(req.body)
                print("Using req.body")
            except:
                print("req.body is not valid JSON or dict")
        
        # Method 2: Try req.payload
        if payload is None and hasattr(req, 'payload'):
            try:
                if isinstance(req.payload, dict):
                    payload = req.payload
                elif isinstance(req.payload, str):
                    payload = json.loads(req.payload)
                print("Using req.payload")
            except:
                print("req.payload is not valid JSON or dict")
        
        # Method 3: Try req itself
        if payload is None:
            try:
                # Check if req has get method like a dict
                if hasattr(req, 'get') and callable(getattr(req, 'get')):
                    payload = req
                    print("Using req object as payload")
            except:
                print("req is not dict-like")
        
        # Print what we found
        print(f"Final payload type: {type(payload)}")
        if payload:
            if isinstance(payload, dict):
                print(f"Payload keys: {list(payload.keys())}")
            else:
                print(f"Payload: {repr(payload)}")
        
        # Extract data from payload if possible
        if isinstance(payload, dict):
            message = payload.get('message', '')
            conversation_history = payload.get('conversation_history', [])
            user_style_preferences = payload.get('user_style_preferences', {})
            selected_stylebot = payload.get('selected_stylebot', 'lexi')
        
        # If we couldn't extract a message, return an error
        if not message:
            return res.json({
                "error": "Message is required and could not be found in request"
            }, 400)
        
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
        
        # Return response to client using Appwrite's res.json()
        return res.json({
            "response": {
                "message": ai_message,
                "conversation_id": str(int(time.time()))
            }
        })
        
    except Exception as e:
        print(f"Error processing StyleBot request: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return res.json({
            "error": "Sorry, StyleBot is having trouble right now. Please try again in a moment."
        }, 500)

def create_system_prompt(user_preferences: Dict, stylist_personality: str) -> str:
    prompt = f"{stylist_personality}\n\n"
    
    prompt += "Your goal is to provide style advice and fashion recommendations in a conversational manner. "
    prompt += "Focus on engaging, personalized fashion advice that matches the user's preferences. "
    
    # Add user preferences to the prompt if available
    if user_preferences.get("aesthetics"):
        prompt += f"The user's aesthetic preferences include: {', '.join(user_preferences['aesthetics'])}. "
    
    if user_preferences.get("brands"):
        prompt += f"Their favorite brands include: {', '.join(user_preferences['brands'])}. "
    
    if user_preferences.get("keyPieces"):
        prompt += f"Key pieces in their wardrobe: {', '.join(user_preferences['keyPieces'])}. "
    
    if user_preferences.get("styleGoal"):
        prompt += f"Their style goal is: {user_preferences['styleGoal']}. "
    
    # Add guidelines for responses
    prompt += "\n\nGuidelines for your responses:"
    prompt += "\n- Keep responses concise and focused on fashion advice"
    prompt += "\n- Provide specific, actionable styling suggestions"
    prompt += "\n- Recommend outfit combinations that match the user's aesthetic"
    prompt += "\n- If asked about a specific clothing item, suggest ways to style it"
    prompt += "\n- If the user mentions colors, suggest color combinations"
    prompt += "\n- Consider current fashion trends while respecting the user's preferences"
    prompt += "\n- Be enthusiastic and encouraging about the user's style journey"
    
    return prompt

def get_stylebot_personality(stylebot_id: str) -> str:
    personalities = {
        'lexi': "You are Lexi, a cheerful and candid fashion assistant. Your tone is upbeat and friendly, with a dash of playfulness. You're knowledgeable about current trends but also appreciate timeless pieces. You speak like a supportive friend who's excited to help style outfits.",
        
        'stella': "You are Stella, a trendy fashion assistant who stays on the cutting edge. Your tone is cool and confident, with an eye for the latest styles. You love experimenting with fashion and encourage users to step out of their comfort zone, while still respecting their personal style.",
        
        'vivi': "You are Vivi, a confident and fashion-forward assistant. Your tone is sophisticated and polished, with authoritative style knowledge. You focus on creating cohesive, well-put-together looks that make a statement, and you value quality over quantity.",
        
        'bella': "You are Bella, an energetic and upbeat fashion assistant. Your tone is enthusiastic and encouraging, making styling fun and accessible. You're great at mixing high and low pieces and finding budget-friendly alternatives to trending styles."
    }
    
    return personalities.get(stylebot_id, personalities['lexi'])  # Default to Lexi if not found
