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
ignore_file = os.path.join(dir_path, '.gitignore')
create_folder(image_path)

PARAMS = {
    'action': 'query',
    'format': 'json',
    'prop': 'imageinfo',
    'iiprop': 'url|size|mime|timestamp',
    'generator': 'search',
    'gsrsearch': 'street art london',
    'gsrlimit': '2500',
    'gsrnamespace': '6',
}

response = requests.get(URL, headers=headers, params=PARAMS)
data = response.json()
print(response.content)

downloaded_images = 0
max_images = 2500
allpages = {}

while downloaded_images < max_images:
    response = requests.get(URL, headers=headers, params=PARAMS)
    data = response.json()

    if 'query' not in data:
        break

    pages = data['query']['pages']
    for page_id, page_data in pages.items():
        if downloaded_images >= max_images:
            break

        image_info = page_data.get('imageinfo', [])[0]
        if not image_info:
            continue

        image_url = image_info['url']
        if not image_url:
            continue

        image_name = os.path.basename(image_url)
        image_filepath = os.path.join(image_path, image_name)
        image_response = requests.get(url=image_url, headers=headers)

        if "image" not in image_response.headers.get("Content-Type", ""):
            print("doesn't point to an image")
            continue

        if image_response.status_code == 200:
            try:
                image = Image.open(io.BytesIO(image_response.content))
                image.save(image_filepath)
                downloaded_images += 1
                allpages[image_name] = True
                with open(ignore_file, 'a') as f:
                    f.write(f"{image_name}\n")
            except UnidentifiedImageError:
                print(f"Cannot identify image file {image_name}, skipping.")
                continue
    if 'continue' in data and 'gsroffset' in data['continue']:
        PARAMS['gsroffset'] = data['continue']['gsroffset']
        print(data.keys())
    else:
        print("No more pages to fetch.")
        break

