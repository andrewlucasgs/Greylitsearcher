import streamlit as st
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, parse_qs
import time

def build_google_search_url(site_search=None, all_words="", exact_phrase="", at_least_one="", without_words="", date_range_start="", date_range_end="", start_page=0):
    base_url = "https://www.google.com/search?q="
    query_parts = []

    if site_search:
        sites = " OR ".join([f"site:{site.strip()}" for site in site_search.split('\n') if site.strip()])
        query_parts.append(sites)

    if all_words:
        query_parts.append("+".join(all_words.split()))

    if exact_phrase:
        query_parts.append(f'"{"+".join(exact_phrase.split())}"')

    if at_least_one:
        or_words = " OR ".join(at_least_one.split())
        query_parts.append(or_words)

    if without_words:
        query_parts.extend([f"-{word}" for word in without_words.split()])

    tbs = ""
    if date_range_start and date_range_end:
        tbs = f"&tbs=cdr:1,cd_min:{date_range_start.replace('-', '/')},cd_max:{date_range_end.replace('-', '/')}"

    start = ""
    if start_page > 0:
        start = f"&start={start_page * 10}"

    return base_url + "+".join(query_parts) + tbs + start

def fetch_html(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None

def extract_google_search_results(html):
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for a in soup.find_all('a', href=True):
        title_element = a.find('h3')
        if not title_element:
            continue

        title = title_element.get_text()

        parsed_href = urlsplit(a['href'])
        link = parse_qs(parsed_href.query).get('q')
        if link:
            link = link[0]
            domain = urlsplit(link).netloc
        else:
            continue

        description = None
        sibling = a.find_next_sibling()
        if sibling and not sibling.find('h3'):
            description = sibling.get_text(strip=True)
        elif a.parent:
            sibling = a.parent.find_next_sibling()
            if sibling and not sibling.find('h3'):
                description = sibling.get_text(strip=True)

        date = None
        if description:
            date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', description)
            if date_match:
                date = date_match.group(0)

        results.append({
            'title': title,
            'link': link,
            'description': description,
            'domain': domain,
            'date': date,
        })

    return results

st.set_page_config(layout="wide")
st.title('Greylitsearcher')

with st.sidebar:
    st.header('Search Criteria')
    site_search = st.text_area("Site Search (one per line)")
    all_words = st.text_input("All these words")
    exact_phrase = st.text_input("This exact word or phrase")
    at_least_one = st.text_input("Any of these words")
    without_words = st.text_input("None of these words")
    date_range_start = st.text_input("Date range start (YYYY-MM-DD)")
    date_range_end = st.text_input("Date range end (YYYY-MM-DD)")
    number_of_pages = st.number_input("Number of pages to search", min_value=1, value=1)
    search_button = st.button('Search')

if search_button:
    all_results = []
    status_text = st.empty()
    results_placeholder = st.empty()

    for page in range(number_of_pages):
        status_text.write(f"Fetching page {page + 1} of {number_of_pages}...")

        if page > 0:
            time.sleep(3)  # Be polite with Google's servers

        search_url = build_google_search_url(site_search, all_words, exact_phrase, at_least_one, without_words, date_range_start, date_range_end, page)
        html = fetch_html(search_url)

        if html is None:
            break  # If there's an error, stop fetching more pages

        page_results = extract_google_search_results(html)
        all_results.extend(page_results)

        # Display results for each page as they are fetched
        df_results = pd.DataFrame(all_results)
        results_placeholder.dataframe(df_results)

        if len(page_results) == 0:
            break  # If no results are found on the current page, stop fetching more pages

    if all_results:
        status_text.write(f"Search completed. Found {len(all_results)} results.")
        csv = df_results.to_csv(index=False)
        st.download_button("Download search results as CSV", csv, "google_search_results.csv", "text/csv", key='download-csv')
    else:
        st.write("No results found or there was an error fetching the results.")
