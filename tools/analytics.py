import streamlit as st
from streamlit.components.v1 import html

def inject_ga():
    GA_JS = '''
    <html>
        <head>
            <!-- Google tag (gtag.js) -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-7BZWCYKNKP"></script>
            <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'G-7BZWCYKNKP');
            </script>
        </head>
    </html>
    '''

    html(GA_JS, height=0)