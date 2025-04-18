import os
import json
import requests

def main(context):
    api_user   = os.environ['SIGHTENGINE_USER']
    api_secret = os.environ['SIGHTENGINE_SECRET']

    try:
        data = json.loads(context.req.body)
        text = data.get("text")
        if not text:
            return context.res.json({
                'success': False,
                'message': 'No text provided.'
            })

        # Build the form data
        payload = {
            'text': text,
            'mode': 'standard',               # or 'ml' for the ML models
            'models': 'profanity,personal',   # comma‑separated models
            'lang': 'en,es,pt,fr,it',
            'api_user': api_user,
            'api_secret': api_secret
        }

        # POST directly to Sightengine’s text API
        resp = requests.post(
            'https://api.sightengine.com/1.0/text/check.json',
            data=payload
        )
        output = resp.json()

        # Now do exactly the same checks on output['profanity']['matches'], etc.
        is_appropriate = True
        reason = None
        for match in output.get('profanity', {}).get('matches', []):
            if match['intensity'] > 0.7:
                is_appropriate = False
                reason = "Text contains inappropriate content"
                break
        if is_appropriate:
            for match in output.get('personal', {}).get('matches', []):
                if match['intensity'] > 0.7:
                    is_appropriate = False
                    reason = "Text contains personal information"
                    break

        return context.res.json({
            'success': True,
            'is_appropriate': is_appropriate,
            'reason': reason,
            'details': {
                'profanity_matches': output.get('profanity', {}).get('matches', []),
                'personal_matches': output.get('personal',  {}).get('matches', [])
            }
        })

    except Exception as e:
        return context.res.json({
            'success': False,
            'message': f'Error: {e}'
        })
