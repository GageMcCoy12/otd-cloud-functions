from sightengine.client import SightengineClient
import base64
import os
from io import BytesIO

def main(req, res):
    # get api keys from environment variables (we'll set these in appwrite)
    api_user = os.environ.get('SIGHTENGINE_USER')
    api_secret = os.environ.get('SIGHTENGINE_SECRET')

    try:
        # get the base64 image from the request
        image_data = req.payload.get('image')
        if not image_data:
            return res.json({
                'success': False,
                'message': 'no image provided bestie'
            })

        # init sightengine client
        client = SightengineClient(api_user, api_secret)

        # analyze the image
        output = client.check('nudity', 'wad', 'offensive').set_bytes(base64.b64decode(image_data))

        # set our thresholds for what we consider safe
        is_safe = (
            output['nudity']['safe'] > 0.7 and  # high confidence it's safe
            output['weapon'] < 0.4 and          # low chance of weapons
            output['drugs'] < 0.4 and           # low chance of drugs
            output['offensive']['prob'] < 0.4    # low chance of offensive content
        )

        # detailed response so we know why something was flagged
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

        return res.json(response)

    except Exception as e:
        return res.json({
            'success': False,
            'message': f'oof something went wrong: {str(e)}'
        })
