import streamlit as st
import random
import base64
import pandas as pd
from libgen_api import LibgenSearch
from deta import Deta
import time

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
    file_ = open(random_image_filename, "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()
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

def display_results(results):
    for i, book in enumerate(results, start=1):
        download_links = s.resolve_download_links(book)

        # Columns for response
        left, right = st.columns([3, 1], gap="small")

        left.caption(f"**Year:** {book['Year']}&emsp;**Size:** {book['Size']}&emsp;**Extension**: {book['Extension']}")
        left.write(f"[**{book['Title']}**]({list(download_links.values())[1]})")  # Hyperlink the book title with the Cloudflare link
        left.write(f"*{book['Author']}*")

        # Display the download links as "Link 1", "Link 2", "Link 3"
        for i, value in enumerate(download_links.values(), start=1):
            right.markdown(f"[Download Link {i}]({value})")
        st.divider()
    
    # record query into db
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    querydb.put({"search_type": search_type, "pdf_only": pdf_only, "english_only": english_only, "query": query, "time": current_time})
    # db_content = db.fetch().items
    # st.write(db_content)

# Search options
search_type = st.radio(
    "Search by:",
    ["Book Title", "Author"],
    index=0, horizontal=True)

# Search query input
query = st.text_input(f"Search {search_type.lower()}:", help="Search is case and symbol sensitive")

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
    results = search_books(search_type, query)
    if results:
        # Create a new dataframe with only the desired columns
        new_results = pd.DataFrame(
            results, columns=['Author', 'Title', 'Publisher', 'Year', 'Size', 'Extension'])
        new_results['Year'].fillna('NA', inplace=True)

        st.info(f"Showing results for {len(results)} items.")
        # st.dataframe(new_results, use_container_width=True) ## df of the results
        st.divider()

        display_results(results)
    else:
        st.info("None found. Please try again.")

# Hide made with Streamlit footer and top-right main menu button
hide_streamlit_style = """
            <style>
            stSidebar {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
