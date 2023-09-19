import requests
from bs4 import BeautifulSoup

def libgen_image(item):
    ''' Returns the image url of the cover of the
        request.
    '''
    page = requests.get(item["Mirror_1"])
    soup = BeautifulSoup(page.text, "html.parser")
    img = soup.find("img", alt="cover")
    domain = page.url.split("//")[1].split("/")[0]
    cover = (f'https://{domain}{img["src"]}')
    return cover