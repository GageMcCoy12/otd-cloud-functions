import os
import json
import requests

def main(context):
    # 1) Grab your Sightengine credentials
    api_user   = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        # 2) Parse incoming JSON
        data = json.loads(context.req.body)
        text = data.get("text")
        if not text:
            return context.res.json({
                'success': False,
                'message': 'No text provided.'
            })

        # 3) Build the API payload
        payload = {
            'text':      text,
            'mode':      'standard',              # your required mode
            'models':    'profanity,personal',    # the checks you want
            'lang':      'en,es,pt,fr,it',        # your supported langs
            'api_user':  api_user,
            'api_secret':api_secret
        }

        # 4) Fire off the check
        resp = requests.post(
            'https://api.sightengine.com/1.0/text/check.json',
            data=payload
        )
        output = resp.json()

        # 5) Prep your response shape
        prof_matches = output.get('profanity', {}).get('matches', [])
        pers_matches = output.get('personal',  {}).get('matches', [])
        result = {
            'success':       True,
            'is_appropriate': True,
            'reason':        None,
            'details': {
                'profanity_matches': prof_matches,
                'personal_matches':  pers_matches
            }
        }

        # 6) Map rule-based strings to scores (if 'intensity' is present)
        severity_map = {'low':0.3, 'medium':0.6, 'high':0.9}

        # 7) Block on profanity if score > 0.7
        for m in prof_matches:
            if 'intensity' in m:
                val = m['intensity']
                score = severity_map[val] if isinstance(val, str) else float(val)
            else:
                # no intensity field? assume a hit is severe
                score = 1.0
            if score > 0.7:
                result['is_appropriate'] = False
                result['reason'] = "Text contains inappropriate content"
                break

        # 8) If still clean, block on *any* personal-info match
        if result['is_appropriate'] and pers_matches:
            result['is_appropriate'] = False
            result['reason'] = "Text contains personal information"

        # 9) Return your structured moderation verdict
        return context.res.json(result)

    except Exception as e:
        # catch everything else
        return context.res.json({
            'success': False,
            'message': f'Error: {e}'
        })
