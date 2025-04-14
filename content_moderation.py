from sightengine.client import SightengineClient
import base64
import os
import re
import json

def main(context):
    # Retrieve API keys from environment variables
    api_user = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        # Parse the JSON body to get the image data
        data = json.loads(context.req.body)
        image_data = data.get("image", None)
        if not image_data:
            return context.res.json({
                'success': False,
                'message': 'No image provided.'
            })
        
        # Remove data URI header if present (e.g., "data:image/jpeg;base64,")
        image_data = re.sub(r'^data:image\/\w+;base64,', '', image_data)
        
        # Decode the base64 image data to bytes
        decoded_bytes = base64.b64decode(image_data)
        
        # Check if the decoded image bytes are valid (non-empty)
        if len(decoded_bytes) == 0:
            return context.res.json({
                'success': False,
                'message': 'Decoded image is empty.'
            })
        
        # Initialize the SightEngine client
        client = SightengineClient(api_user, api_secret)
        
        # Analyze the image using SightEngine's content moderation
        output = client.check('nudity', 'wad', 'offensive').set_bytes(decoded_bytes)
        
        # Evaluate safety based on defined thresholds
        is_safe = (
            output['nudity']['raw'] < 0.4 and
            output['nudity']['partial'] < 0.7 and
            output['weapon'] < 0.4 and
            output['drugs'] < 0.4 and
            output['offensive']['prob'] < 0.4
        )

        
        # Prepare detailed response with moderation scores
        response = {
            'success': True,
            'is_safe': is_safe,
            'details': {
                'nudity_score': output['nudity'],
                'weapon_score': output['weapon'],
                'drugs_score': output['drugs'],
                'offensive_score': output['offensive']
            }
        }
        
        return context.res.json(response)

    except Exception as e:
        return context.res.json({
            'success': False,
            'message': f'Error: {str(e)}'
        })
