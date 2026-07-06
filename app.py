import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# --- Page Configuration ---
st.set_page_config(page_title="UN HDR Intelligence", page_icon="🌍", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Tighten top padding */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    /* Style the metric containers */
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #1E3A8A; }
    [data-testid="stMetricLabel"] { font-weight: bold; color: #475569; }
    /* Custom subheaders */
    h3 { color: #0F172A; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🌍 UN Human Development Report Intelligence")
st.markdown("**Country Focus:** Philippines (2005) | **Data Extraction:** Llama 3 | **Evaluation:** Mistral")
st.divider()

# --- Load Data ---
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

# --- KPI Cards Layer ---
indicators = data[0]['extraction'].get('numerical_indicators', {})

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    hdi_val = indicators.get('HDI_value', 'N/A')
    st.metric(label="Human Development Index", value=hdi_val)
with col_k2:
    rank_val = indicators.get('HDI_rank', 'N/A')
    st.metric(label="Global Rank", value=rank_val)
with col_k3:
    life_val = indicators.get('life_expectancy_years', 'N/A')
    st.metric(label="Life Expectancy (Years)", value=life_val)
with col_k4:
    gni_val = indicators.get('gni_per_capita', 'N/A')
    # Format GNI to look like currency if it's a number
    gni_formatted = f"${gni_val:,.0f}" if isinstance(gni_val, (int, float)) else gni_val
    st.metric(label="GNI per Capita", value=gni_formatted)

st.markdown("<br>", unsafe_allow_html=True)

# --- Main Visualizations Layer ---
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("1. Thematic Distribution Focus")
    # Upgrade: Horizontal bar chart, sorted for readability, cleaner color scale
    df_themes = pd.DataFrame(list(themes.items()), columns=['Theme', 'Mentions']).sort_values(by='Mentions', ascending=True)
    fig1 = px.bar(df_themes, x='Mentions', y='Theme', orientation='h', 
                  color='Mentions', color_continuous_scale='Blues')
    fig1.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("2. Time-Series Demographic Trends")
    if trends:
        # Upgrade: Smooth spline lines, filled area under the curve, improved markers
        df_trends = pd.DataFrame(trends)
        fig2 = px.line(df_trends, x='year', y='value', color='metric_name', markers=True)
        fig2.update_traces(line_shape='spline', fill='tozeroy', marker=dict(size=8))
        fig2.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=30, b=0), 
                           xaxis_title="Year", yaxis_title="Percentage (%)", legend_title="")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No time-series trends extracted from the sample chunks.")

st.markdown("<br>", unsafe_allow_html=True)
col3, col4 = st.columns(2, gap="large")

with col3:
    st.subheader("3. Core Indicator Footprint (Radar)")
    # Upgrade: Cleaner radar layout, filled area
    hdi = indicators.get('HDI_value')
    life = indicators.get('life_expectancy_years')
    school = indicators.get('expected_years_of_schooling')
    
    hdi_val = (hdi if hdi is not None else 0) * 100
    life_val = life if life is not None else 0
    school_val = (school if school is not None else 0) * 5
    
    categories = ['HDI Value (x100)', 'Life Expectancy', 'Schooling (x5)']
    values = [hdi_val, life_val, school_val]
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatterpolar(
        r=values + [values[0]], # Close the loop
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(30, 58, 138, 0.4)',
        line=dict(color='#1E3A8A', width=2),
        marker=dict(size=8)
    ))
    fig3.update_layout(
        template="plotly_white",
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values)+10])), 
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30)
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("4. LLM Quality Evaluation (Mistral)")
    # Upgrade: Bar chart for scores instead of a boxplot (which looks empty with only 1 data point)
    avg_scores = {
        "Consistency": sum(eval_scores["Consistency"]) / len(eval_scores["Consistency"]) if eval_scores["Consistency"] else 0,
        "Completeness": sum(eval_scores["Completeness"]) / len(eval_scores["Completeness"]) if eval_scores["Completeness"] else 0,
        "Factual Alignment": sum(eval_scores["Factual Alignment"]) / len(eval_scores["Factual Alignment"]) if eval_scores["Factual Alignment"] else 0
    }
    df_eval = pd.DataFrame(list(avg_scores.items()), columns=['Metric', 'Score (out of 10)'])
    
    fig4 = px.bar(df_eval, x='Metric', y='Score (out of 10)', color='Metric',
                  color_discrete_sequence=['#10B981', '#F59E0B', '#3B82F6'], text_auto=True)
    fig4.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=30, b=0), 
                       yaxis=dict(range=[0, 10]), showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --- Qualitative Highlights Layer ---
st.subheader("Qualitative Extraction Highlights")
col_q1, col_q2 = st.columns(2)

with col_q1:
    # Upgrade: Use Streamlit's success box for positive attributes
    with st.container():
        st.markdown('#### ✅ Key Strengths')
        for s in data[0]['extraction'].get('key_strengths', []):
            st.success(s)

with col_q2:
    # Upgrade: Use Streamlit's warning box for negative attributes
    with st.container():
        st.markdown('#### ⚠️ Key Challenges')
        for c in data[0]['extraction'].get('key_challenges', []):
            st.warning(c)
