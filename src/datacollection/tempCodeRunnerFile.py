import requests
import os 
from PIL import Image, UnidentifiedImageError
import io 

URL = 'https://commons.wikimedia.org/w/api.php'

headers = {"User-Agent": "1testproj/1.0 (https://example.com; pakhi141102@gmail.com)"}

def create_folder(folder_name):
    check_folder = os.path.isdir(folder_name)
    if not check_folder:
        os.makedirs(folder_name)

dir_path = os.path.dirname(os.path.realpath(__file__))
image_path = os.path.join(dir_path, 'C:/Users/pakhi/OneDrive/Documents/art-style-ai/data/images')
create_folder(image_path)

PARAMS = {
    'action': 'query',
    'format': 'json',
    'prop': 'imageinfo',
    'iiprop': 'url|size|mime|timestamp',
    'generator': 'search',
    'gsrsearch': 'london street art',
    'gsrlimit': '2500',
    'gsrnamespace': '6',
}

response = requests.get(URL, headers=headers, params=PARAMS)
data = response.json()
print(response.content)

# downloaded_images = 0
# max_images = 2500
# allpages = {}

# while downloaded_images < max_images:
#     response = requests.get(URL, headers=headers, params=PARAMS)
#     data = response.json()

#     if 'query' not in data:
#         break
