from deta import Deta
import streamlit as st
import time

def query2db(search_type, pdf_only, english_only, query):
    # Connect to Deta Base with your Data Key
    deta = Deta(st.secrets["data_key"])

    # Create a new database
    querydb = deta.Base("ultrasearch-queries")

    # record query into the database
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    querydb.put({"search_type": search_type, "pdf_only": pdf_only, "english_only": english_only, "query": query, "time": current_time})