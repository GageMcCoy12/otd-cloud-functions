 from sightengine.client import SightengineClient
import base64
import os
import json
from io import BytesIO

def main(context):
    # get api keys from environment variables (we'll set these in appwrite)
    api_user = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        print("DEBUG: Starting content moderation...")
        
        # get the base64 image from the request body
        body_str = context.req.body
        print(f"DEBUG: Raw body type: {type(body_str)}")
        print(f"DEBUG: Raw body: {body_str[:100]}...") # print first 100 chars
        
        # Parse the body - it's already a string, so we just need to parse it as JSON
        body = json.loads(body_str)
        print(f"DEBUG: Parsed body keys: {body.keys()}")
        
        image_data = body['image']  # use direct key access since we know it should be there
        if not image_data:
            return context.res.json({
                'success': False,
                'message': 'no image provided bestie'
            })

        print("DEBUG: Got image data, initializing SightEngine...")
        
        # Clean up base64 data - remove any prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Ensure padding is correct
        padding = len(image_data) % 4
        if padding:
            image_data += '=' * (4 - padding)

        try:
            # Decode base64 to binary
            binary_image = base64.b64decode(image_data)
            print(f"DEBUG: Successfully decoded base64 data, size: {len(binary_image)} bytes")
        except Exception as e:
            print(f"DEBUG: Failed to decode base64: {str(e)}")
            return context.res.json({
                'success': False,
                'message': 'failed to decode image data'
            })
        
        # init sightengine client
        client = SightengineClient(api_user, api_secret)

        # analyze the image
        print("DEBUG: Analyzing image with SightEngine...")
        try:
            output = client.check('nudity', 'wad', 'offensive').set_bytes(binary_image)
            print(f"DEBUG: Got SightEngine response: {output}")
        except Exception as e:
            print(f"DEBUG: SightEngine API error: {str(e)}")
            return context.res.json({
                'success': False,
                'message': f'SightEngine API error: {str(e)}'
            })

        # set our thresholds for what we consider safe
        # SightEngine returns probabilities between 0 and 1
        is_safe = (
            output.get('nudity', {}).get('raw', 0) < 0.4 and      # low chance of nudity
            output.get('weapon', 0) < 0.4 and                      # low chance of weapons
            output.get('drugs', 0) < 0.4 and                       # low chance of drugs
            output.get('offensive', {}).get('prob', 0) < 0.4       # low chance of offensive content
        )

        # detailed response so we know why something was flagged
        response = {
            'success': True,
            'is_safe': is_safe,
            'details': {
                'nudity': output.get('nudity', {}),
                'weapon': output.get('weapon', 0),
                'drugs': output.get('drugs', 0),
                'offensive': output.get('offensive', {})
            }
        }
        print(f"DEBUG: Sending response: {response}")

        return context.res.json(response)

    except Exception as e:
        print(f"DEBUG: Error occurred: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return context.res.json({
            'success': False,
            'message': f'oof something went wrong: {str(e)}'
        }) 
