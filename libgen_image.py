import requests
from bs4 import BeautifulSoup
import urllib.request

def libgen_image(item):
    ''' Returns the image url of the cover of the
        request.
    '''
    page = requests.get(item["Mirror_1"])

    soup = BeautifulSoup(page.text, "lxml")  # Use the lxml parser
    img = soup.find("img", alt="cover")
    domain = page.url.split("//")[1].split("/")[0]

    urllib.request.urlretrieve(f'https://{domain}{img["src"]}', "temp_image.jpg")
    return "temp_image.jpg"