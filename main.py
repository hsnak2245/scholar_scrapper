import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
import pyperclip  # For copying content to clipboard

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyC6gs5gBMoR40vZXD_fn5NGpk7o6tUZ_RU"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Page configuration
st.set_page_config(
    page_title="Scholar Profile Analyzer & Email Assistant",
    page_icon="📚",
    layout="wide"
)

# Function to scrape and analyze Google Scholar profile
def scrape_and_analyze_profile(author_url, selected_details):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(author_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

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
        st.error(f"Error: {e}")
        return None

def generate_detailed_summary(author_info, publications, selected_details):
    """Generate detailed summary based on selected details"""
    summary = []

    if 'name' in selected_details:
        summary.append(f"Name: {author_info['name']}\n")

    if 'affiliation' in selected_details:
        summary.append(f"Affiliation: {author_info['affiliation']}\n")

    if 'summary' in selected_details and author_info['summary']:
        summary.append(f"Summary: {author_info['summary']}\n")

    if 'interests' in selected_details and author_info['interests']:
        summary.append(f"Research Interests: {', '.join(author_info['interests'])}\n")

    if 'metrics' in selected_details and author_info['metrics']:
        metrics = author_info['metrics']
        summary.append(f"Citations: {metrics.get('Citations', '0')}\n")
        summary.append(f"h-index: {metrics.get('h-index', '0')}\n")
        summary.append(f"i10-index: {metrics.get('i10-index', '0')}\n")

    if 'publications' in selected_details and publications:
        summary.append("\nTop Publications:\n")
        sorted_pubs = sorted(publications, key=lambda x: x['citations'], reverse=True)
        for pub in sorted_pubs[:5]:
            summary.append(f"• {pub['title']} ({pub['year']}) - {pub['citations']} citations\n")

    return '\n'.join(summary)

def customize_email(template, context, comments):
    """Customize email using Gemini API"""
    try:
        prompt = f"""
        Email Template:
        {template}

        Recipient Context (Author Info):
        {context}

        Additional Comments:
        {comments}

        Please customize this email template based on the recipient context and any additional comments provided.
        Make sure to maintain a professional tone while personalizing the content.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error customizing email: {str(e)}"

# Streamlit UI
st.title("📚 Scholar Profile & Email Customizer")

# Tabs for different functionalities
tab1, tab2 = st.tabs(["Scholar Profile Analyzer", "Email Customizer"])

# Scholar Profile Analyzer Tab
with tab1:
    st.header("📚 Scholar Profile Analyzer")

    scholar_url = st.text_input(
        "Enter Google Scholar Profile URL",
        placeholder="https://scholar.google.com/citations?user=..."
    )

    # Select the details to be included
    details = st.multiselect(
        "Select details to include in analysis:",
        ["name", "affiliation", "summary", "interests", "metrics", "publications"],
        default=["name", "affiliation", "metrics"]
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Analyze Profile", type="primary"):
            if scholar_url:
                with st.spinner("Analyzing profile..."):
                    # Step 1: Scrape and analyze the profile
                    summary = scrape_and_analyze_profile(scholar_url, details)

                    if summary:
                        st.session_state.current_summary = summary
                        st.success("Profile analyzed successfully!")
                    else:
                        st.error("Failed to analyze profile")
            else:
                st.warning("Please enter a Google Scholar URL")

    # Display results
    if 'current_summary' in st.session_state:
        st.header("Analysis Results")
        st.text_area("Profile Summary", st.session_state.current_summary, height=300)

        # Copy button
        if st.button("Copy Summary to Clipboard"):
            pyperclip.copy(st.session_state.current_summary)
            st.success("Profile Summary copied to clipboard")

# Email Customizer Tab
with tab2:
    st.header("✉️ Email Customizer")

    email_template = st.text_area(
        "Email Template",
        height=200,
        placeholder="Enter your email template here..."
    )

    additional_comments = st.text_area(
        "Additional Comments",
        height=100,
        placeholder="Any additional instructions or comments..."
    )

    if st.button("Generate Email"):
        if 'current_summary' in st.session_state and email_template:
            with st.spinner("Customizing email..."):
                email_context = st.session_state.current_summary
                customized_email = customize_email(email_template, email_context, additional_comments)
                st.session_state.customized_email = customized_email

                # Display the customized email
                st.header("Customized Email")
                st.text_area("Result", value=customized_email, height=300)

                # Copy button for email
                if st.button("Copy Customized Email to Clipboard"):
                    pyperclip.copy(customized_email)
                    st.success("Customized Email copied to clipboard")

    else:
        st.warning("Please provide both email template and profile context.")
        
# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, Google Scholar, and Gemini AI")
