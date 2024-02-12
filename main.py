
import streamlit as st
import requests
import re
import pandas as pd
# import bs4
from bs4 import BeautifulSoup


def build_google_search_url(
    site_search=None, all_words="", exact_phrase="", at_least_one="", without_words="",
    date_range_start="", date_range_end="", start_page=0
):
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
        response.raise_for_status()  # This will ensure that HTTP error responses, like 404 or 500, raise exceptions.
        return response.text
    except requests.RequestException as e:
        return f"An error occurred: {e}"

from urllib.parse import urlsplit, parse_qs

def extract_google_search_results(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for a in soup.find_all('a', href=True):
        title_element = a.find('h3')
        if not title_element:
            continue  # Skip any 'a' elements that do not contain an 'h3' child

        title = title_element.get_text()

        # Attempt to extract the actual link from the 'a' tag's 'href' attribute
        parsed_href = urlsplit(a['href'])
        link = parse_qs(parsed_href.query).get('q')
        if link:
            link = link[0]  # Extract the first item from the list if present
            domain = urlsplit(link).netloc
        else:
            continue  # Skip if no link is found

        # Description extraction is tricky without reliable classes; this approach tries to find a sibling or parent's sibling
        description = None
        sibling = a.find_next_sibling()
        if sibling and not sibling.find('h3'):
            description = sibling.get_text(strip=True) 
        elif a.parent:
            sibling = a.parent.find_next_sibling()
            if sibling and not sibling.find('h3'):
                description = sibling.get_text(strip=True)

        # extract date from description, usually in the format "Apr 12, 2022" or "3 days ago"      
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
            'search_url': parsed_href.geturl(),
        })

    return results

st.set_page_config(layout="wide")


# Streamlit app starts here
st.title('Greylitsearcher')

# Using sidebar for input controls
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

    # Search button in sidebar
    search_button = st.button('Search')

# import time
import time

# Main area for displaying results and download button
if search_button:
    results = []
    search_urls = []

    # Placeholder for displaying messages and the results table
    status_placeholder = st.empty()
    current_search_url_placeholder = st.empty()
    results_placeholder = st.empty()

    for page in range(number_of_pages):
        # Sleep 3s between requests to avoid being blocked by Google
        if page > 0:
            status_placeholder.write(f"Sleeping for 3 seconds before fetching page {page + 1}...")
            time.sleep(3)
        status_placeholder.write(f"Fetching page {page + 1} of {number_of_pages}...")
        
        start_page = page
        search_url = build_google_search_url(
            site_search=site_search, all_words=all_words, exact_phrase=exact_phrase,
            at_least_one=at_least_one, without_words=without_words,
            date_range_start=date_range_start, date_range_end=date_range_end, start_page=start_page
        )
        current_search_url_placeholder.write('Fetching: ' + search_url)
        search_urls.append(search_url)
        if page == 0:
            # Display search URL only for the first page to avoid clutter
            status_placeholder.write('Search URL: ' + search_url)

        html = fetch_html(search_url)
        page_results = extract_google_search_results(html)
        # include a column for the search URL
        for result in page_results:
            result['search_url'] = search_url
        results.extend(page_results)

        # Update the results table with new data after each page is fetched
        if page_results:
            df_results = pd.DataFrame(results)
            results_placeholder.dataframe(df_results[['title', 'link', 'description', 'domain', 'date', 'search_url']])

        if page == number_of_pages - 1:
            status_placeholder.write(f"Search completed. Fetched {len(results)} results from {number_of_pages} pages.")

    if len(results) > 0:
        # Convert DataFrame to CSV for download after all results are fetched
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="Download search results as CSV",
            data=csv,
            file_name='google_search_results.csv',
            mime='text/csv',
        )
    else:
        status_placeholder.write("No results found.")