import json
import os
import time
import base64
import requests
from typing import Dict, List, Any

def main(context):
    print("StyleBot function started")
    
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        print("ERROR: OpenAI API key not found in environment variables")
        return context.res.json({
            'success': False,
            'error': "StyleBot is not properly configured. Please contact support."
        }, 500)
    
    request_data = context.req.body
    print(f"Raw request data received (details omitted for brevity)")
    
    if isinstance(request_data, str):
        try:
            request_data = json.loads(request_data)
            print(f"Request data parsed successfully")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return context.res.json({
                'success': False,
                'error': f'Error parsing JSON request: {str(e)}'
            }, 400)
    
    try:
        message = request_data.get('message', '')
        conversation_history = request_data.get('history', [])
        user_style_preferences = request_data.get('userPreferences', {})
        selected_stylebot = request_data.get('selected_stylebot', 'lexi')
        image_base64 = request_data.get('image', None)
        
        if not message:
            print("No message found in request")
            return context.res.json({
                'success': False,
                'error': "Message is required"
            }, 400)
        
        print(f"Processing message: {message}")
        print(f"Selected StyleBot: {selected_stylebot}")
        print(f"Image included: {'Yes' if image_base64 else 'No'}")
        
        formatted_history = []
        for msg in conversation_history:
            if isinstance(msg, dict):
                formatted_history.append({
                    "role": "user" if msg.get("isUser") else "assistant",
                    "content": msg.get("text", "")
                })
        
        stylist_personality = get_stylebot_personality(selected_stylebot)
        system_prompt = create_system_prompt(user_style_preferences, stylist_personality)
        
        if image_base64:
            print("Image detected, using vision capabilities...")
            user_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
            
            messages = [
                {"role": "system", "content": system_prompt + "\n\nThe user has shared an image of their outfit or clothing item. Analyze the image and provide specific style advice based on what you see."},
                *formatted_history,
                user_message
            ]
            
            model = "gpt-4o"
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                *formatted_history,
                {"role": "user", "content": message}
            ]
            
            model = "gpt-4o-mini"
        
        print(f"Calling OpenAI API with model: {model}...")
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.95
            }
        )
        
        response.raise_for_status()
        response_data = response.json()
        ai_message = response_data['choices'][0]['message']['content']
        
        print(f"AI response received: {ai_message[:50]}...")
        
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
    prompt += "Your goal is to provide engaging, personalized style advice in a friendly, casual tone using plain text. "
    prompt += "Keep responses short and conversational, avoiding markdown formatting. "
    prompt += "Use lowercase text and casual slang naturally. "
    prompt += "Ask follow-up questions before finalizing outfit recommendations. "
    prompt += "Channel the laid-back, authentic energy of Emma Chamberlain and Billie Eilish.\n\n"
    
    if user_preferences.get("aesthetics"):
        prompt += "User's aesthetic preferences: " + ", ".join(user_preferences['aesthetics']) + ".\n"
    if user_preferences.get("brands"):
        prompt += "Favorite brands: " + ", ".join(user_preferences['brands']) + ".\n"
    if user_preferences.get("keyPieces"):
        prompt += "Wardrobe key pieces: " + ", ".join(user_preferences['keyPieces']) + ".\n"
    if user_preferences.get("styleGoal"):
        prompt += "Style goal: " + user_preferences['styleGoal'] + ".\n"
    
    prompt += "\nGuidelines:\n"
    prompt += "- Ask follow-up questions if needed.\n"
    prompt += "- Use a conversational tone with casual language.\n"
    prompt += "- Avoid markdown formatting.\n"
    prompt += "- Provide specific, actionable styling suggestions.\n"
    
    return prompt

def get_stylebot_personality(stylebot_id: str) -> str:
    personalities = {
        'lexi': "You are Lexi, a cheerful and candid fashion assistant. Your tone is upbeat and friendly, with a dash of playfulness. You're knowledgeable about current trends but also appreciate timeless pieces. You speak like a supportive friend who's excited to help style outfits.",
        'stella': "You are Stella, a trendy fashion assistant who stays on the cutting edge. Your tone is cool and confident, with an eye for the latest styles. You love experimenting with fashion and encourage users to step out of their comfort zone, while still respecting their personal style.",
        'vivi': "You are Vivi, a confident and fashion-forward assistant. Your tone is sophisticated and polished, with authoritative style knowledge. You focus on creating cohesive, well-put-together looks that make a statement, and you value quality over quantity.",
        'bella': "You are Bella, an energetic and upbeat fashion assistant. Your tone is enthusiastic and encouraging, making styling fun and accessible. You're great at mixing high and low pieces and finding budget-friendly alternatives to trending styles."
    }
    
    return personalities.get(stylebot_id, personalities['lexi'])
