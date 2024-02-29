import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

def download_image(item):
    '''Function to download a single image and return its content.'''
    image_content = None
    with requests.Session() as session:
        page = session.get(item["Mirror_1"])
        soup = BeautifulSoup(page.content, "lxml")
        img = soup.find("img", alt="cover")
        if img:
            domain = page.url.split("//")[1].split("/")[0]
            image_url = f'https://{domain}{img["src"]}'

            # Download image
            with session.get(image_url, stream=True) as r:
                r.raise_for_status()
                image_content = r.content  # Store the image content in memory

    return image_content

def libgen_images(items):
    '''Runs image downloads in parallel for each item in items and collects them.'''
    images = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_image, item) for item in items]
        for future in futures:
            image_content = future.result()  # Wait for all futures to complete
            if image_content:
                images.append(image_content)  # Collect the image content

    return images

# Split the download-image function to get urls and download images
# Run get urls first and run that as fast as possible
# Run image downloads to the speed bs4 allows it to.
# still return it via memory.