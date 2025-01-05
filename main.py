import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Scholar Profile Analyzer",
    page_icon="📚",
    layout="wide"
)

def scrape_and_analyze_profile(author_url, selected_details):
    """
    Scrape and analyze a Google Scholar profile based on the user's selected details.
    Returns both raw data and analyzed summary.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(author_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract author details
        author_info = {
            'name': soup.find('div', id='gsc_prf_in').text if soup.find('div', id='gsc_prf_in') else None,
            'affiliation': soup.find('div', class_='gsc_prf_il').text if soup.find('div', class_='gsc_prf_il') else None,
            'interests': [tag.text for tag in soup.find_all('a', class_='gsc_prf_inta')],
            'metrics': {},
            'summary': soup.find('div', class_='gsc_prf_il').text if soup.find('div', class_='gsc_prf_il') else None
        }

        # Extract citation metrics
        metrics_table = soup.find('table', id='gsc_rsb_st')
        if metrics_table:
            for row in metrics_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    metric_name = cells[0].text.strip()
                    metric_value = cells[1].text.strip()
                    author_info['metrics'][metric_name] = metric_value

        # Extract publications
        publications = []
        pubs = soup.find_all('tr', class_='gsc_a_tr')

        for pub in pubs:
            title_element = pub.find('a', class_='gsc_a_at')
            authors_element = pub.find('div', class_='gs_gray')
            venue_element = pub.find_all('div', class_='gs_gray')
            year_element = pub.find('span', class_='gsc_a_h')
            citations_element = pub.find('a', class_='gsc_a_ac')

            if title_element:
                citations = citations_element.text if citations_element else '0'
                citations = int(citations) if citations.isdigit() else 0

                year = year_element.text if year_element else None
                year = int(year) if year and year.isdigit() else 0

                publication = {
                    'title': title_element.text,
                    'authors': authors_element.text if authors_element else None,
                    'venue': venue_element[1].text if len(venue_element) > 1 else None,
                    'year': year,
                    'citations': citations,
                }
                publications.append(publication)

        return generate_detailed_summary(author_info, publications, selected_details)

    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_detailed_summary(author_info, publications, selected_details):
    """
    Generate a detailed textual summary of the author's academic profile.
    Return summary based on selected details.
    """
    summary = []

    # Include name if selected
    if 'name' in selected_details:
        summary.append(f"Name: {author_info['name']}\n")

    # Include affiliation if selected
    if 'affiliation' in selected_details and author_info['affiliation']:
        summary.append(f"Affiliation: {author_info['affiliation']}\n")

    # Include summary (profile overview) if selected
    if 'summary' in selected_details and author_info['summary']:
        summary.append(f"Summary: {author_info['summary']}\n")

    # Include interests (keywords) if selected
    if 'interests' in selected_details and author_info['interests']:
        summary.append(f"Research Interests/Keywords: {', '.join(author_info['interests'])}\n")

    # Include citation metrics if selected
    if 'metrics' in selected_details and author_info['metrics']:
        metrics = author_info['metrics']
        citation_summary = f"Citations: {metrics.get('Citations', '0')}, H-index: {metrics.get('h-index', '0')}, i10-index: {metrics.get('i10-index', '0')}\n"
        summary.append(citation_summary)

    # Include publications if selected
    if 'publications' in selected_details and publications:
        summary.append("\nPublications:\n")
        for pub in publications[:5]:  # Display top 5 publications
            summary.append(f"• {pub['title']} ({pub['year']}) - {pub['citations']} citations\n")

    return '\n'.join(summary)

def save_summary(summary, filename):
    """
    Save the summary to a text file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(summary)

# Main app interface
st.title("📚 Scholar Profile Analyzer")

# Input section
col1, col2 = st.columns([2, 1])
with col1:
    scholar_url = st.text_input(
        "Enter Google Scholar Profile URL",
        placeholder="https://scholar.google.com/citations?user=..."
    )

    # Select details to include in the analysis
    details = st.multiselect(
        "Select details to include in the analysis:",
        ["name", "affiliation", "summary", "interests", "metrics", "publications"]
    )

    if st.button("Analyze Profile", type="primary"):
        if scholar_url:
            with st.spinner("Analyzing profile..."):
                try:
                    summary = scrape_and_analyze_profile(scholar_url, details)
                    if summary:
                        st.session_state.current_summary = summary
                        st.success("Profile analyzed successfully!")
                    else:
                        st.error("Failed to analyze profile. Please check the URL and try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a Google Scholar URL")

# Display analysis results
if 'current_summary' in st.session_state:
    st.header("Analysis Results")
    st.markdown(st.session_state.current_summary)
    
    # Option to copy the analysis as text
    st.text_area("Copy the analysis:", st.session_state.current_summary, height=300)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export as TXT"):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scholar_summary_{timestamp}.txt"
            save_summary(st.session_state.current_summary, filename)
            st.success(f"Exported to {filename}")

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ using Streamlit and Google Scholar"
)
