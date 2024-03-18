import pandas as pd
import streamlit as st
import requests

# Search engine CXs
GS_CX = [
    st.secrets['GS1_CX'],
    st.secrets['GS1_CX'],
    st.secrets['GS1_CX']
]

# API keys
GS_KEYS = [
    st.secrets['GS1_KEY'],
    st.secrets['GS2_KEY'],
    st.secrets['GS3_KEY'],
]


def google_search(page, site, **kwargs):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': '',
        'key': '',
        'cx': '',
        'num': 10,
        'start': page * 10 + 1,
        'siteSearch': site
    }
    params.update(kwargs)
    for cx, key in zip(GS_CX, GS_KEYS):
        params['cx'] = cx
        params['key'] = key
        # return {'items': [{'link': 'https://www.google.com'}]}
        response = requests.get(url, params=params).json()
        # Check if the response is successful or if the rate limit has been exceeded
        if not response.get('error') or 'rateLimitExceeded' not in response['error']['errors'][0]['reason']:
            return response
    # If all keys exceeded the rate limit, print an error message
    print("All keys have exceeded the rate limit.")
    return None


st.set_page_config(layout="wide", page_title="Greylitsearcher",
                   page_icon="🔍️",)
st.title('Greylitsearcher')
st.write("""
Greylitsearcher is a tool that helps you find grey literature on the web.\n
You can get up to 40 results from each website. If the first search doesn't give you enough results, it will keep searching until it finds up to 40.
""")


with st.expander("Search 1", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        and1 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and1')
        exact1 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact1')
    with col2:
        any1 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any1')
        none1 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none1')

with st.expander("Search 2"):
    col3, col4 = st.columns(2)
    with col3:
        and2 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and2')
        exact2 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact2')
    with col4:
        any2 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any2')
        none2 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none2')

with st.expander("Search 3"):
    col5, col6 = st.columns(2)
    with col5:
        and3 = st.text_input(
            "All these words", help="Appends the specified query terms to the query, as if they were combined with a logical AND operator.", key='and3')
        exact3 = st.text_input("This exact word or phrase",
                               help="Identifies a phrase that all documents in the search results must contain.", key='exact3')
    with col6:
        any3 = st.text_input(
            "Any of these words", help="Provides additional search terms to check for in a document, where each document in the search results must contain at least one of the additional search terms.", key='any3')
        none3 = st.text_input(
            "None of these words", help="Identifies a word or phrase that should not appear in any documents in the search results.", key='none3')

websites = st.text_area("Websites to search",
                        key='websites',
                        help="Enter one website per line",
                        placeholder="example.com\nexample2.com"
                        )


search_button = st.button('Search')


limitExceeded = False

if search_button:
    st.session_state['results'] = {}
    websites = websites.split('\n')
    for website in websites:
        if website:
            st.session_state['results'][website] = []
            for page in range(4):
                current_results = google_search(
                    page, website, q=and1, exactTerms=exact1, orTerms=any1, excludeTerms=none1)
                if current_results == None:
                    limitExceeded = True
                    break
                for item in current_results.get('items', []):
                    item['priority'] = 1

                st.session_state['results'][website].extend(
                    current_results.get('items', []))
                if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                    break
            if len(st.session_state['results'][website]) < 40 and (and2 or exact2 or any2 or none2):
                for page in range(8):
                    current_results = google_search(
                        page, website, q=and2, exactTerms=exact2, orTerms=any2, excludeTerms=none2)
                    if current_results == None:
                        limitExceeded = True
                        break
                    for item in current_results.get('items', []):
                        item['priority'] = 2

                    st.session_state['results'][website].extend([item for item in current_results.get(
                        'items', []) if item['link'] not in [i['link'] for i in st.session_state['results'][website]]])

                    if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                        break
            if len(st.session_state['results'][website]) < 40 and (and3 or exact3 or any3 or none3):
                for page in range(10):
                    current_results = google_search(
                        page, website, q=and3, exactTerms=exact3, orTerms=any3, excludeTerms=none3)
                    if current_results == None:
                        limitExceeded = True
                        break
                    for item in current_results.get('items', []):
                        item['priority'] = 3
                    st.session_state['results'][website].extend([item for item in current_results.get(
                        'items', []) if item['link'] not in [i['link'] for i in st.session_state['results'][website]]])

                    if len(st.session_state['results'][website]) >= 40 or len(current_results.get('items', [])) < 10:
                        break
            st.session_state['results'][website] = st.session_state['results'][website][:40]

if 'results' in st.session_state.keys():
    for website in st.session_state['results']:
        cols = st.columns(2)
        with cols[0]:
            st.write(
                f"{len(st.session_state['results'][website])} results for {website}")
        with cols[1]:
            df = pd.DataFrame(st.session_state['results'][website])
            csv = df.to_csv(index=False)
            btn = st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name=f"{website.replace('.', '_')}_results.csv",
                mime="text/csv"
            )
        st.dataframe(st.session_state['results'][website],
                    use_container_width=True
                    )
        if limitExceeded:
            st.write('Rate limit exceeded. Please try again later.')
