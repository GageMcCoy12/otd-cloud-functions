import json
import os
import time
import base64
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
    print(f"Raw request data received (details omitted for brevity)")
    
    # Parse the JSON string if it's a string
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
        # Extract data from payload
        message = request_data.get('message', '')
        conversation_history = request_data.get('conversation_history', [])
        user_style_preferences = request_data.get('user_style_preferences', {})
        selected_stylebot = request_data.get('selected_stylebot', 'lexi')
        image_base64 = request_data.get('image', None)
        
        # If we couldn't extract a message, return an error
        if not message:
            print("No message found in request")
            return context.res.json({
                'success': False,
                'error': "Message is required"
            }, 400)
        
        print(f"Processing message: {message}")
        print(f"Selected StyleBot: {selected_stylebot}")
        print(f"Image included: {'Yes' if image_base64 else 'No'}")
        
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
        if image_base64:
            # If image is included, use the vision model with image content
            print("Image detected, using vision capabilities...")
            
            # Prepare the user message with image
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
            
            # Use GPT-4 Vision for image analysis
            model = "gpt-4o"
        else:
            # Standard text-only conversation
            messages = [
                {"role": "system", "content": system_prompt},
                *formatted_history,
                {"role": "user", "content": message}
            ]
            
            # Use a smaller model for text-only conversations
            model = "gpt-4o-mini"
        
        print(f"Calling OpenAI API with model: {model}...")
        
        # Call OpenAI API
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
    prompt += "\n- When analyzing images, be specific about the items you see and provide tailored advice"
    prompt += "\n- Comment on fit, color combinations, and styling options based on the shared image"
    
    return prompt

def get_stylebot_personality(stylebot_id: str) -> str:
    personalities = {
        'lexi': "You are Lexi, a cheerful and candid fashion assistant. Your tone is upbeat and friendly, with a dash of playfulness. You're knowledgeable about current trends but also appreciate timeless pieces. You speak like a supportive friend who's excited to help style outfits.",
        
        'stella': "You are Stella, a trendy fashion assistant who stays on the cutting edge. Your tone is cool and confident, with an eye for the latest styles. You love experimenting with fashion and encourage users to step out of their comfort zone, while still respecting their personal style.",
        
        'vivi': "You are Vivi, a confident and fashion-forward assistant. Your tone is sophisticated and polished, with authoritative style knowledge. You focus on creating cohesive, well-put-together looks that make a statement, and you value quality over quantity.",
        
        'bella': "You are Bella, an energetic and upbeat fashion assistant. Your tone is enthusiastic and encouraging, making styling fun and accessible. You're great at mixing high and low pieces and finding budget-friendly alternatives to trending styles."
    }
    
    return personalities.get(stylebot_id, personalities['lexi'])  # Default to Lexi if not found
