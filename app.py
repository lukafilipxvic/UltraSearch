import streamlit as st
import random
import base64
import pandas as pd
from libgen_api import LibgenSearch
from deta import Deta
import time
from libgen_image import libgen_image
import hide_st
import requests
from bs4 import BeautifulSoup

st.set_page_config(
    layout="centered",
    page_title="UltraSearch",
    page_icon="🔎",
    initial_sidebar_state="collapsed",
)

## Fix this major libgen-api error >>> IndexError: list index out of range

# Google Analytics
ga_code = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7BZWCYKNKP"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-7BZWCYKNKP');
</script>"""
st.markdown(ga_code, unsafe_allow_html=True)

# Connect to Deta Base with your Data Key
deta = Deta(st.secrets["data_key"])

# Create a new databases
querydb = deta.Base("ultrasearch-queries")
#linkdb = deta.Base("ultrasearch-links") need to create db.put code below

# Function to randomly get data_url for image
@st.cache_data(ttl=60)
def rnd_image_load():
    image_filenames = ["images/books.webp",
                    "images/magnifying-glass-tilted-left.webp",
                    "images/magnifying-glass-tilted-right.webp",
                    ]
    random_image_filename = random.choice(image_filenames)
    with open(random_image_filename, "rb") as file_:
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
    return data_url

# Load the images and display it
colA, colB = st.columns([0.2,0.3])

# Display the random image
data_url = rnd_image_load()
colA.markdown(
    f'<img src="data:image/gif;base64,{data_url}" alt="random image" width="65" height="65" style="float: right; margin-top: 20px;">',
    unsafe_allow_html=True)

# Heading of App
colB.header('UltraSearch')

# Create an instance of LibgenSearch
s = LibgenSearch()

def search_books(search_type, query):
    if search_type == "Author" and filters:
        results = s.search_author_filtered(query, filters, exact_match=False)
    elif search_type == "Author" and not filters:
        results = s.search_author(query)
    elif search_type == "Book Title" and filters:
        results = s.search_title_filtered(query, filters, exact_match=False)
    elif search_type == "Book Title" and not filters:
        results = s.search_title(query)

    filtered_results = []
    for book in results:
        if (not pdf_only or book['Extension'] == 'pdf') and (not english_only or book['Language'] == 'English'):
            filtered_results.append(book)
    return filtered_results

def resolve_download_links(item):
    MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io", "Pinata"] # libgen-api doesn't get the Pinata link
    mirror_1 = item["Mirror_1"]
    page = requests.get(mirror_1)
    soup = BeautifulSoup(page.text, "html.parser")
    links = soup.find_all("a", string=MIRROR_SOURCES)
    download_links = {link.string: link["href"] for link in links}
    return download_links

def display_results(results):
    for i, book in enumerate(results, start=1):
        with st.spinner(f'Gathering knowledge... &emsp; {i}/{len(results)}'):
            download_links = resolve_download_links(book)
            image_path = libgen_image(book)

            # Columns for response
            left, mid, right = st.columns([0.8, 3, 1], gap="small")

            left.image(image_path)

            mid.caption(f"**Year:** {book['Year']}&emsp;**Pages:** {book['Pages']}&emsp;**Size:** {book['Size']}&emsp;**Extension**: {book['Extension']}")
            mid.write(f"[**{book['Title']}**]({list(download_links.values())[0]})")  # Hyperlink the book title with the library.lol link
            mid.write(f"*{book['Author']}*")

            # Display the download links as "Link 1", "Link 2", "Link 3"
            for i, value in enumerate(download_links.values(), start=1):
                right.markdown(f"[Download Link {i}]({value})")
            st.divider()
    
    # record query into db
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    #querydb.put({"search_type": search_type, "pdf_only": pdf_only, "english_only": english_only, "query": query, "time": current_time})
    # db_content = db.fetch().items
    # st.write(db_content)

# Search options
search_type = st.radio(
    "Search by:",
    ["Book Title", "Author"],
    index=0, horizontal=True)

# Search query input
query = st.text_input(f"Search {search_type.lower()}:", help="Search is case and symbol sensitive.")

# Filters for search
col1, col2 = st.columns([0.2,0.8], gap="small")

pdf_only = col1.checkbox('PDFs only', value=True)
english_only = col2.checkbox('English Only', value=True)
filters = {}

if pdf_only:
    filters['Extension'] = 'pdf'
if english_only:
    filters['Language'] = 'English'

# Search button
if query:
    with st.spinner('Searching...'):
        results = search_books(search_type, query)
    if results:
        # Create a new dataframe with only the desired columns
        new_results = pd.DataFrame(
            results, columns=['Author', 'Title', 'Publisher', 'Year', 'Size', 'Extension'])
        new_results['Year'].fillna('NA', inplace=True)

        st.info(f"Showing results for {len(results)} items")
        # st.dataframe(new_results, use_container_width=True) ## df of the results
        st.divider()
        display_results(results)
    else:
        st.info("None found. Please try again.")


# Hide made with Streamlit footer and top-right main menu button
hide_st.header()
hide_st.footer()

st.markdown("""
            <div id="div"></div>
            <script>
                window.addEventListener('message', (event) => {
                    // Replace 'http://127.0.0.1:5500/site/index.html' with the origin of your parent page
                    if (event.origin !== "http://127.0.0.1:5500/site/index.html") {
                        return; // Ignore messages from unknown origins for security
                    }

                    if (event.data.action === 'removeElement') {
                        const element = document.querySelector(event.data.selector);
                        if (element) {
                            element.parentNode.removeChild(element);
                        }
                    }
                });
            </script>
            """,
            unsafe_allow_html=True)