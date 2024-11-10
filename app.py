import streamlit as st
import random
import base64
import pandas as pd
from libgen_api import LibgenSearch
from tools.libgen_image import libgen_image
import tools.hide_st as hide_st
import stealth_requests as requests
from bs4 import BeautifulSoup

st.set_page_config(
    layout="centered", page_title="UltraSearch", page_icon="🔎",
    initial_sidebar_state="collapsed")

# Function to randomly get data_url for image
@st.cache_data(ttl=60)
def rnd_image_load():
    image_filenames = ["images/books-ultra.webp",
                    "images/left-search-ultra.webp",
                    "images/right-search-ultra.webp",
                    ]
    random_image_filename = random.choice(image_filenames)
    with open(random_image_filename, "rb") as file_:
        contents = file_.read()
        data_url = base64.b64encode(contents).decode("utf-8")
    return data_url

colA, colB, colC = st.columns([0.2, 0.6, 0.2])

data_url = rnd_image_load()
colB.markdown(
    f'''
    <img src="data:image/gif;base64,{data_url}" alt="UltraSearch Logo" style="width: 100%; height: auto; margin-top: calc(20%); margin-bottom: 5%;">
    ''',
    unsafe_allow_html=True)
colB.write()

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
        if (file_type == 'Any' or (file_type == 'EPUBs only' and book['Extension'] == 'epub') or (file_type == 'PDFs only' and book['Extension'] == 'pdf')) and (not english_only or book['Language'] == 'English'):
            filtered_results.append(book)
    return filtered_results

def resolve_download_links(item):
    MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io", "Pinata"]
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
            mid.write(f"[**{book['Title']}**]({list(download_links.values())[0]})")
            mid.write(f"*{book['Author']}*")

            # Display the download links as "Link 1", "Link 2", "Link 3"
            for i, value in enumerate(download_links.values(), start=1):
                right.markdown(f"[Download Link {i}]({value})")
            st.divider()
    


col1, col2, col3 = st.columns([0.32, 0.45, 0.2], gap="small")

search_type = col1.radio("Search by:", ["Book Title", "Author"], index=0, horizontal=True, label_visibility="collapsed")
file_type = col2.radio('File Extension:', ['Any', 'EPUBs only', 'PDFs only'], index=0, horizontal=True, label_visibility="collapsed")
english_only = col3.checkbox('English Only', value=True)

query = st.text_input(label=f"Search {search_type.lower()}:",
                        placeholder=f"Search {search_type.lower()}",
                        help="Search is case and symbol sensitive.",
                        label_visibility="collapsed")


filters = {}

if file_type == 'EPUBs only':
    filters['Extension'] = 'epub'
elif file_type == 'PDFs only':
    filters['Extension'] = 'pdf'
if english_only:
    filters['Language'] = 'English'

if st.button("Search"):
    with st.spinner('Searching...'):
        results = search_books(search_type, query)
    if results:
        new_results = pd.DataFrame(
            results, columns=['Author', 'Title', 'Publisher', 'Year', 'Size', 'Extension'])
        new_results.fillna({'Year':'NA'}, inplace=True)

        st.info(f"Showing results for {len(results)} items")
        # st.dataframe(new_results, use_container_width=True) ## df of the results
        st.divider()
        display_results(results)
    else:
        st.info("None found. Please try again.")


# Hide made with Streamlit footer and top-right main menu button
#hide_st.header()
hide_st.footer()