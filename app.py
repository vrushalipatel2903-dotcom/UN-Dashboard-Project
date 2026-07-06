import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="UN HDR Dashboard", layout="wide")
st.title("🌍 UN Human Development Report Intelligence Dashboard")

# Load Data
@st.cache_data
def load_data():
    with open('processed_report_data.json', 'r') as f:
        return json.load(f)

data = load_data()

# --- Data Aggregation ---
themes = {"education": 0, "health": 0, "inequality": 0, "economy": 0, "gender": 0, "climate": 0, "employment": 0}
eval_scores = {"Consistency": [], "Completeness": [], "Factual Alignment": []}
trends = []

for item in data:
    chunk_themes = item['extraction'].get('themes_distribution', {})
    for k in themes.keys():
        themes[k] += chunk_themes.get(k, 0)
    
    ev = item['evaluation']
    eval_scores['Consistency'].append(ev.get('consistency_score', 0))
    eval_scores['Completeness'].append(ev.get('completeness_score', 0))
    eval_scores['Factual Alignment'].append(ev.get('factual_alignment_score', 0))
    trends.extend(item['extraction'].get('demographic_trends', []))

# --- Dashboard Layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Thematic Distribution")
    df_themes = pd.DataFrame(list(themes.items()), columns=['Theme', 'Mentions'])
    fig1 = px.bar(df_themes, x='Theme', y='Mentions', color='Theme', title="Frequency of Key Themes")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("2. Quality Evaluation Metrics")
    df_eval = pd.DataFrame(eval_scores)
    fig2 = px.box(df_eval, title="Mistral's Evaluation of Llama3's Extraction")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("3. Demographic Trends Over Time")
    if trends:
        df_trends = pd.DataFrame(trends)
        fig3 = px.line(df_trends, x='year', y='value', color='metric_name', markers=True, title="Key Development Trends")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No time-series trends extracted from the sample chunks.")

with col4:
    st.subheader("4. Core Development Indicators (Radar)")
    indicators = data[0]['extraction'].get('numerical_indicators', {})
    
    # SAFELY handle nulls to prevent the white screen crash, and scale values for visuals
    hdi = indicators.get('HDI_value')
    life = indicators.get('life_expectancy_years')
    school = indicators.get('expected_years_of_schooling')
    
    hdi_val = (hdi if hdi is not None else 0) * 100
    life_val = life if life is not None else 0
    school_val = (school if school is not None else 0) * 5
    
    categories = ['HDI Value (Scaled)', 'Life Expectancy', 'Schooling (Scaled)']
    values = [hdi_val, life_val, school_val]
    
    fig4 = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))
    fig4.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False, title="Indicator Footprint")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.subheader("Qualitative Highlights")

st.write("**Key Strengths:**")
for s in data[0]['extraction'].get('key_strengths', []):
    st.write(f"- {s}")

st.write("**Key Challenges:**")
for c in data[0]['extraction'].get('key_challenges', []):
    st.write(f"- {c}")
