import streamlit as st
import time
import random
import base64
from deta_db import query2db
import pandas as pd
from libgen_api import LibgenSearch
from libgen_images import libgen_images, download_image
import hide_st
import requests
from bs4 import BeautifulSoup

st.set_page_config(
    layout="centered", page_title="UltraSearch", page_icon="🔎",
    initial_sidebar_state="collapsed")

# Function to randomly get data_url for image
@st.cache_data(ttl=60)
def rnd_image_load():
    image_filenames = ["images/books-ultra.webp",
                    "images/left-search-ultra.webp",
                    "images/right-search-ultra.webp"]
    random_image_filename = random.choice(image_filenames)
    with open(random_image_filename, "rb") as file_:
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
    return data_url

colA, colB, colC = st.columns([0.2, 0.6, 0.2])

data_url = rnd_image_load()
colB.markdown(
    f'<img src="data:image/gif;base64,{data_url}" alt="UltraSearch Logo" style="width: 100%; height: auto; margin-top: calc(20%); margin-bottom: 5%;">',
    unsafe_allow_html=True)

def search_books(search_type, query):
    # Create an instance of LibgenSearch
    s = LibgenSearch()

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
    # Hide query2db to disable query recording to Deta.
    #query2db(search_type, pdf_only, english_only, query)
    #with st.spinner('Getting images...'):
    #    start = time.time()
    #    book_covers = libgen_images(results)


    for i, book in enumerate(results):
        with st.spinner(f'Gathering knowledge... &emsp; {i+1}/{len(results)}'):
            download_links = resolve_download_links(book)
            book_cover = download_image(results[i])
            # Columns for response
        left, mid, right = st.columns([0.8, 3, 1], gap="small")
        left.image(image=book_cover, width=100)

        mid.caption(f"**Year:** {book['Year']}&emsp;**Pages:** {book['Pages']}&emsp;**Size:** {book['Size']}&emsp;**Extension**: {book['Extension']}")
        mid.write(f"[**{book['Title']}**]({list(download_links.values())[1]})")  # Hyperlink the book title with the Cloudflare ipfs link
        mid.write(f"*{book['Author']}*")
        # Display the download links as "Link 1", "Link 2", "Link 3"
        for i, value in enumerate(download_links.values(), start=1):
            right.markdown(f"[Download Link {i}]({value})")
        st.divider()


# Search options
search_type = st.radio("Search by:", ["Book Title", "Author"], index=0, horizontal=True)

# Search query input
query = st.text_input(label=f"Search {search_type.lower()}:",
                        placeholder=f"Search {search_type.lower()}",
                        help="Search is case and symbol sensitive.",
                        label_visibility="collapsed")

# Filters for search
col1, col2, col3 = st.columns([0.2,0.2,0.5], gap="small")

pdf_only = col1.checkbox('PDFs only', value=False)
english_only = col2.checkbox('English Only', value=True)
filters = {}

if pdf_only:
    filters['Extension'] = 'pdf'
if english_only:
    filters['Language'] = 'English'

if query:
    with st.spinner('Searching...'):
        results = search_books(search_type, query)
    if results:
        # Create a new dataframe with only the desired columns
        new_results = pd.DataFrame(
            results, columns=['Author', 'Title', 'Publisher', 'Year', 'Size', 'Extension'])
        new_results.fillna({'Year':'NA'}, inplace=True)

        st.info(f"Showing results for {len(results)} items")
        # st.dataframe(new_results, use_container_width=True) ## df of the results
        st.divider()
        start = time.time()
        display_results(results)
        end = time.time()
        colB.write(f"({end-start:.2f} seconds)")
    else:
        st.info("None found. Please try again.")


# Hide made with Streamlit footer and top-right main menu button
hide_st.header()
hide_st.footer()