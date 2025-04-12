import os
import requests

# Create the directory for Vazirmatn fonts if it doesn't exist
os.makedirs('static/fonts/vazirmatn', exist_ok=True)

# List of Vazirmatn font weights to download
font_weights = [
    'Thin',
    'ExtraLight',
    'Light',
    'Regular',
    'Medium',
    'SemiBold',
    'Bold',
    'ExtraBold',
    'Black'
]

# Base URL for the font files on GitHub
base_url = 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/webfonts'

# Download each font file
for weight in font_weights:
    font_url = f'{base_url}/Vazirmatn-{weight}.woff2'
    font_path = f'static/fonts/vazirmatn/Vazirmatn-{weight}.woff2'
    
    print(f'Downloading {font_url} to {font_path}...')
    response = requests.get(font_url)
    
    if response.status_code == 200:
        with open(font_path, 'wb') as f:
            f.write(response.content)
        print(f'Successfully downloaded {font_path}')
    else:
        print(f'Failed to download {font_url}: {response.status_code}')

print('Done downloading Vazirmatn fonts!') 