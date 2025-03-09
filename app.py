import streamlit as st
import asyncio
import random
import base64
from libgen_api_modern import LibgenSearch
import pandas as pd
from tools.image_downloader import async_download_image
import tools.hide_st as hide_st
import aiohttp
import os
import uuid
from pathlib import Path

# Create downloads directory if it doesn't exist
os.makedirs("downloads", exist_ok=True)

st.set_page_config(
    layout="centered", page_title="UltraSearch", page_icon="🔎",
    initial_sidebar_state="collapsed")

@st.cache_data(ttl=600)
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
    <img src="data:image/gif;base64,{data_url}" alt="UltraSearch Logo" style="width: 100%; height: auto; margin-top: calc(15%); margin-bottom: 10%;">
    ''',
    unsafe_allow_html=True)
colB.write()

s = LibgenSearch()

# Initialize session states
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'downloading_books' not in st.session_state:
    st.session_state.downloading_books = {}
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'search_params' not in st.session_state:
    st.session_state.search_params = {
        'search_type': 'Title',
        'query': '',
        'file_type': 'Any',
        'english_only': True
    }
if 'book_images' not in st.session_state:
    st.session_state.book_images = {}

async def search_books(search_type: str, query: str, file_type: str, english_only: bool) -> list[dict]:
    filters = {}
    if search_type in ["Author", "Title"] and filters:
        results = await s.search_filtered(query, filters, search_type=search_type.lower(), exact_match=False)
    elif search_type in ["Author", "Title"] and not filters:
        results = await s.search(query, search_type=search_type.lower())

    filtered_results = []
    for book in results:
        if (file_type == 'Any' or 
            (file_type == 'EPUBs only' and book['Extension'].lower() == 'epub') or 
            (file_type == 'PDFs only' and book['Extension'].lower() == 'pdf')) and (not english_only or book['Language'] == 'English'):
            filtered_results.append(book)
    return filtered_results

async def download_image(url: str, book_id: str):
    """Download an image and cache it in session state to avoid redownloading."""
    # Check if image is already in session state
    if book_id in st.session_state.book_images:
        return st.session_state.book_images[book_id]
        
    # If not, download and store it
    image_path = await async_download_image(url)
    st.session_state.book_images[book_id] = image_path
    return image_path

async def secure_download_book(url: str, book_title: str, extension: str):
    """
    Downloads a book from the provided URL to the server first, then serves it to the user.
    Returns the local path to the downloaded file.
    """
    # Generate a safe filename using book title and a unique identifier
    safe_filename = f"{uuid.uuid4()}_{book_title.replace(' ', '_')[:50]}.{extension}"
    local_path = os.path.join("downloads", safe_filename)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=120) as response:
                if response.status == 200:
                    with open(local_path, 'wb') as file:
                        while chunk := await response.content.read(1024):
                            file.write(chunk)
                    return local_path
                else:
                    return None
    except Exception as e:
        st.error(f"Download error: {str(e)}")
        return None

# Clean up downloads directory on startup (to prevent accumulation of files)
def cleanup_downloads():
    download_dir = Path("downloads")
    if download_dir.exists():
        for file in download_dir.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                except Exception:
                    pass

@st.fragment
async def handle_book_download(book, book_id):
    """Fragment that handles the downloading of a book without causing a full page rerun."""
    download_key = f"download_{book_id}"
    save_key = f"save_{book_id}"
    
    # Check if this book is already in the downloading process
    if book_id in st.session_state.downloading_books:
        download_state = st.session_state.downloading_books[book_id]
        
        # If we already have the file downloaded, show the download button
        if download_state.get('file_ready'):
            file_data = download_state.get('file_data')
            file_name = download_state.get('file_name')
            mime_type = download_state.get('mime_type')
            
            st.success(f"Download ready")
            # If user downloads or we clear the state, remove from session
            if st.download_button(
                label="Save File",
                data=file_data,
                file_name=file_name,
                mime=mime_type,
                key=save_key
            ):
                # Clear this book from session state after download
                if book_id in st.session_state.downloading_books:
                    del st.session_state.downloading_books[book_id]
            return
    
    # Initial download button
    if st.button("📥 Download", key=download_key):
        with st.spinner("Downloading..."):
            # Try each available download link until one works
            downloaded_file = None
            for j in range(1, 4):
                link_key = f"Direct Download Link {j}"
                if link_key in book and book[link_key]:
                    downloaded_file = await secure_download_book(
                        book[link_key], 
                        book['Title'], 
                        book['Extension'].lower()
                    )
                    if downloaded_file:
                        break
            
            if downloaded_file:
                with open(downloaded_file, "rb") as file:
                    file_bytes = file.read()
                    file_name = os.path.basename(downloaded_file)
                    mime_type = f"application/{book['Extension'].lower()}"
                    
                    # Store file data in session state
                    st.session_state.downloading_books[book_id] = {
                        'file_ready': True,
                        'file_data': file_bytes,
                        'file_name': file_name,
                        'mime_type': mime_type
                    }
                    
                    st.success(f"Download ready")
                    # Create download button
                    if st.download_button(
                        label="Save File",
                        data=file_bytes,
                        file_name=file_name,
                        mime=mime_type,
                        key=save_key
                    ):
                        # Clear this book from session state after download
                        if book_id in st.session_state.downloading_books:
                            del st.session_state.downloading_books[book_id]
                    
                    # Clean up the file after download is initiated
                    try:
                        os.remove(downloaded_file)
                    except:
                        pass
            else:
                st.error("Could not download this book. Please try another source.")
    
    # Optional: Still show the direct links as fallback
    with st.expander("Alternative sources", expanded=False):
        for j in range(0, 4):
            link_key = f"Direct Download Link {j}"
            if link_key in book:
                st.markdown(f"[Link {j}]({book[link_key]})")

@st.fragment
async def search_interface():
    """Fragment handling the search interface and search execution."""
    filters = {}
    col1, col2, col3 = st.columns([0.32, 0.52, 0.18], gap="small")

    # Get values from session state or use defaults
    search_type = col1.radio("Search by:", 
                            ["Title", "Author"], 
                            index=0 if st.session_state.search_params['search_type'] == 'Title' else 1, 
                            horizontal=True, 
                            label_visibility="collapsed",
                            key="search_type_radio")
    
    file_type = col2.radio('File Extension:', 
                          ['Any', 'EPUBs only', 'PDFs only'], 
                          index=['Any', 'EPUBs only', 'PDFs only'].index(st.session_state.search_params['file_type']), 
                          horizontal=True, 
                          label_visibility="collapsed",
                          key="file_type_radio")
    
    english_only = col3.checkbox('English Only', 
                                value=st.session_state.search_params['english_only'],
                                key="english_only_checkbox")

    colX, colY = st.columns([0.999, 0.001], gap="small")

    query = colX.text_input(label=f"Search {search_type}:",
                          placeholder=f"Search {search_type}",
                          value=st.session_state.search_params['query'],
                          help="Search is case and symbol sensitive.",
                          label_visibility="collapsed",
                          key="search_query_input")

    # Update session state with current search parameters
    st.session_state.search_params = {
        'search_type': search_type,
        'query': query,
        'file_type': file_type,
        'english_only': english_only
    }

    if file_type == 'EPUBs only':
        filters['Extension'] = 'epub'
    elif file_type == 'PDFs only':
        filters['Extension'] = 'pdf'
    if english_only:
        filters['Language'] = 'English'

    # Store search parameters to maintain state during fragment reruns
    search_clicked = colY.button("🔎", key="search_button")
    
    # Only execute search when the button is explicitly clicked
    if search_clicked and query:  # Ensure we have a query
        with st.spinner('Searching...'):
            results = await search_books(search_type, query, file_type, english_only)
            # Store in session state for persistence across reruns
            st.session_state.search_results = results
            st.session_state.search_performed = True
    
    return search_clicked

@st.fragment
async def results_display():
    """Fragment handling the display of search results."""
    if st.session_state.search_results:
        results = st.session_state.search_results
        if results:
            # Create DataFrame for potential future use but don't display it
            new_results = pd.DataFrame(results)
            new_results.fillna({'Year':'NA'}, inplace=True)

            st.info(f"Showing results for {len(results)} items")
            st.divider()
            await display_results(results)
        else:
            st.info("None found. Please try again.")
    # When no search has been performed, show nothing
    elif not st.session_state.search_performed:
        pass
    else:
        st.info("Please enter a search query and click the search button.")

async def display_results(results):
    """Display search results and set up UI containers for book information."""
    for i, book in enumerate(results, start=1):
        book_id = f"{book.get('ID', '')}-{i}"
        
        # Create placeholders for the book content
        # We use columns to structure the display
        left_col, mid_col = st.columns([0.8, 3], gap="small")
        
        # Load the image (use cached version if available)
        with st.spinner(f'Gathering knowledge... &emsp; {i}/{len(results)}'):
            image_path = await download_image(book['Cover'], book_id)
            
            # Display book details - this only happens once per book
            with left_col:
                st.image(image_path)
                
            with mid_col:
                st.caption(f"**Year:** {book['Year']}&emsp;**Pages:** {book['Pages']}&emsp;**Size:** {book['Size']}&emsp;**Extension**: {book['Extension']}")
                st.write(f"**{book['Title']}**")
                st.write(f"*{book['Author(s)']}*")
                await handle_book_download(book, book_id)
                
                
        st.divider()

async def main():
    # Call cleanup on startup
    cleanup_downloads()
    
    # Add a clear cache button to the sidebar for troubleshooting
    with st.sidebar:
        st.title("Options")
        if st.button("Clear Cache", key="clear_cache_button"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.search_results = None
            st.session_state.downloading_books = {}
            st.session_state.search_performed = False
            st.session_state.book_images = {}
            st.session_state.search_params = {
                'search_type': 'Title',
                'query': '',
                'file_type': 'Any',
                'english_only': True
            }
            st.cache_data.clear()
            st.rerun()
    
    # Use fragments for search interface and results display
    await search_interface()
    await results_display()

    hide_st.header()
    hide_st.footer()

if __name__ == "__main__":
    # Clean up any leftover downloads from previous sessions
    if not hasattr(st, '_download_cleanup_done'):
        cleanup_downloads()
        st._download_cleanup_done = True
    
    asyncio.run(main())
