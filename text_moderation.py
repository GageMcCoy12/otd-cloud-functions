import os
import json
import requests

def main(context):
    # Retrieve API keys from environment variables
    api_user   = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        # Parse incoming JSON
        data = json.loads(context.req.body)
        text = data.get("text")
        if not text:
            return context.res.json({
                'success': False,
                'message': 'No text provided.'
            })

        # Build the payload for Sightengine Text API
        payload = {
            'text':      text,
            'mode':      'standard',                 # standard
            'models':    'profanity,personal',       # comma-separated models
            'lang':      'en,es,pt,fr,it',           # adjust to your supported langs
            'api_user':   api_user,
            'api_secret': api_secret
        }

        # Call Sightengine Text Moderation endpoint
        resp = requests.post(
            'https://api.sightengine.com/1.0/text/check.json',
            data=payload
        )
        output = resp.json()

        # Severity mapping for rule-based intensities
        severity_map = {
            'low':    0.3,
            'medium': 0.6,
            'high':   0.9
        }

        # Evaluate appropriateness
        is_appropriate = True
        reason = None

        # Check profanity matches
        for match in output.get('profanity', {}).get('matches', []):
            intensity = match['intensity']
            # Convert string labels to numeric, or use float if ML mode
            score = (severity_map[intensity]
                     if isinstance(intensity, str)
                     else float(intensity))
            if score > 0.7:
                is_appropriate = False
                reason = "Text contains inappropriate content"
                break

        # If still appropriate, check personal info matches
        if is_appropriate:
            for match in output.get('personal', {}).get('matches', []):
                intensity = match['intensity']
                score = (severity_map[intensity]
                         if isinstance(intensity, str)
                         else float(intensity))
                if score > 0.7:
                    is_appropriate = False
                    reason = "Text contains personal information"
                    break

        # Return structured moderation response
        return context.res.json({
            'success': True,
            'is_appropriate': is_appropriate,
            'reason': reason,
            'details': {
                'profanity_matches': output.get('profanity', {}).get('matches', []),
                'personal_matches':  output.get('personal',  {}).get('matches', [])
            }
        })

    except Exception as e:
        return context.res.json({
            'success': False,
            'message': f'Error: {e}'
        })
