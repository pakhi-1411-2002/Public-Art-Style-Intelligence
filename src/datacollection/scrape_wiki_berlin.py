import requests 
from PIL import Image, UnidentifiedImageError
import os
import io
import re 

URL = "https://en.wikipedia.org/w/api.php"
Image.MAX_IMAGE_PIXELS = None

headers = {"User-Agent": "1testproj/1.0 (https://example.com; pakhi141102@gmail.com)"}

def sanitize_filename(filename, max_length=100):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename

def is_image_too_large(image_content, max_pixels=15_000_000):
    try:
        image_file = io.BytesIO(image_content)
        with Image.open(image_file) as img:
            width, height = img.size
            if width * height > max_pixels:
                print(f"Skipping huge image ({width}x{height})")
                return True
    except Exception as e:
        print("Error reading image:", e)
        return True
    return False

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
    'gsrsearch': 'street art berlin',
    'gsrlimit': '2500',
    'gsrnamespace': '6',
}

response = requests.get(URL, headers=headers, params=PARAMS)
data = response.json()

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
        image_name = sanitize_filename(image_name)
        image_filepath = os.path.join(image_path, image_name)
        image_response = requests.get(url=image_url, headers=headers)
        
        if not is_image_too_large(image_response):
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
        else:
            print("Image too large, skipping.")

        
    if 'continue' in data:
        PARAMS['gsroffset'] = data['continue']['gsroffset']
        print(data.keys())
    else:
        print("No more pages to fetch.")
        break