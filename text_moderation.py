from sightengine.client import SightengineClient
import os
import json

def main(context):
    # Retrieve API keys from environment variables
    api_user = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        # Parse the JSON body to get the text data
        data = json.loads(context.req.body)
        text = data.get("text", None)
        
        if not text:
            return context.res.json({
                'success': False,
                'message': 'No text provided.'
            })
        
        # Initialize the SightEngine client
        client = SightengineClient(api_user, api_secret)
        
        # Analyze the text using SightEngine's text moderation
        output = client.check('profanity', 'personal').set_text(text)
        
        # Evaluate appropriateness based on defined thresholds
        is_appropriate = True
        reason = None
        
        # Check profanity matches
        if 'profanity' in output and output['profanity']['matches']:
            for match in output['profanity']['matches']:
                if match['intensity'] > 0.7:  # High confidence of profanity
                    is_appropriate = False
                    reason = "Text contains inappropriate content"
                    break
        
        # Check personal information matches
        if 'personal' in output and output['personal']['matches']:
            for match in output['personal']['matches']:
                if match['intensity'] > 0.7:  # High confidence of personal info
                    is_appropriate = False
                    reason = "Text contains personal information"
                    break
        
        # Prepare detailed response with moderation results
        response = {
            'success': True,
            'is_appropriate': is_appropriate,
            'reason': reason,
            'details': {
                'profanity_matches': output.get('profanity', {}).get('matches', []),
                'personal_matches': output.get('personal', {}).get('matches', [])
            }
        }
        
        return context.res.json(response)

    except Exception as e:
        return context.res.json({
            'success': False,
            'message': f'Error: {str(e)}'
        }) 
