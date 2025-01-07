import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import random

st.set_page_config(
    page_title="IELTS Essay Analyzer",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# IELTS Essay Analyzer"
    }
)

st.markdown("""
    <style>
    .error-highlight {
        background-color: #ffcdd2;
        padding: 1px;
        border-radius: 1px;
        cursor: pointer;
    }
    .tooltip {
        position: relative;
        display: inline-block;
    }
            
                .error-highlight {
        background-color: #ffcdd2;
        padding: 1px;
        border-radius: 1px;
        cursor: pointer;
        position: relative;
        display: inline-block;
    }
    
    .error-highlight .tooltip-text {
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: white;
        text-align: center;
        padding: 5px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .error-highlight:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

def highlight_text_with_errors(text, errors):
    highlighted_text = text
    offset = 0
    for error in sorted(errors, key=lambda e: e['start']):
        start = error['start'] + offset
        end = error['end'] + offset
        highlight_html = f"""<span class="error-highlight">
                {text[error['start']:error['end']]}
                <span class="tooltip-text">{error['Description']}</span>
        </span>"""
        highlighted_text = highlighted_text[:start] + highlight_html + highlighted_text[end:]
        offset += len(highlight_html) - (end - start)
    
    return f'<div>{highlighted_text}</div>'

def analyze_essay(text, topic):

    errors = [{'Name': "Task Response", 'Description': "Incorrect verb tense", "start": 25, "end": 30}, 
              {'Name': "Coherence and Cohesion", 'Description': "Missing transition word between ideas", "start": 15, "end": 20},
              {'Name': "Lexical Resource (Vocabulary)", 'Description': "Consider using a more academic word", "start": 40, "end": 50},
              {'Name': "Grammatical Range & Accuracy",'Description': "Bad expression", "start": 10, "end": 15}]
    
    scores = [
        {'Name': "Task Response", 
         'Score': random.uniform(6.0, 9.0), 
         'Errors': [error for error in errors if error['Name'] == "Task Response"], 
         "Exercises": ["Practice using past tense with irregular verbs"]},

        {'Name': "Coherence and Cohesion", 
         'Score': random.uniform(6.0, 9.0), 
         'Errors': [error for error in errors if error['Name'] == "Coherence and Cohesion"], 
         "Exercises": ["Exercise on transition words and phrases"]},

        {'Name': "Lexical Resource (Vocabulary)", 
         'Score': random.uniform(6.0, 9.0), 
         'Errors': [error for error in errors if error['Name'] == "Lexical Resource (Vocabulary)"], 
         "Exercises": ["Practice using past tense with irregular verbs"]},

        {'Name': "Grammatical Range & Accuracy", 
         'Score': random.uniform(6.0, 9.0), 
         'Errors': [error for error in errors if error['Name'] == "Grammatical Range & Accuracy"], 
         "Exercises": ["Practice using past tense with irregular verbs"]}
        ]
        
    
    return scores, errors


def generate_exercises():
    exercises = [
        "Practice using past tense with irregular verbs",
        "Exercise on transition words and phrases",
        "Grammar drill: Subject-verb agreement"
    ]
    return exercises

st.title("IELTS Essay Analyzer")

main_col = st.container()
sidebar = st.sidebar

with main_col:
    essay_topic = st.text_input("Essay Topic")
    
    essay_text = st.text_area("Enter your essay here", height=300)
    
    if st.button("Analyze Essay"):
        if essay_text and essay_topic:
            scores, errors = analyze_essay(essay_text, essay_topic)
            
            st.session_state['scores'] = scores
            st.session_state['errors'] = errors
            
            st.markdown("### Overall Score")
            st.write(f"**{sum(score['Score'] for score in scores) / len(scores)}**")
            for score in scores:
                st.write(f"**{score['Name'].title()}**: {score['Score']}")

            st.markdown("### Your Essay with Annotations")
            highlighted_text = highlight_text_with_errors(essay_text, errors)
            st.markdown(highlighted_text, unsafe_allow_html=True)
            
            st.markdown("### Scores")
            for score in scores:
                with st.expander(label=f"**{score['Name'].title()}** {str(score['Score'])}"):
                    st.write('**Errors:**')
                    for error in score['Errors']:
                        st.write("- " + error['Description'])
                    st.write("**Suggested exercise:**")
                    for ex in score['Exercises']:
                        st.write("- " + ex)
            
            st.markdown("### Recommended Exercises")
            exercises = generate_exercises()
            for ex in exercises:
                st.write("- " + ex)

with sidebar:
    st.markdown("### IELTS Scores")
    if 'scores' in st.session_state:
        scores = st.session_state['scores']
        
        score_df = pd.DataFrame({
            'Criterion': list(scores['Name'] for scores in scores),
            'Score': list(scores['Score'] for scores in scores)
        })
        
        fig = px.bar(score_df, x='Criterion', y='Score',
                    range_y=[0, 9],
                    title='IELTS Assessment')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Progress Over Time")
    progress_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=5),
        'Overall Score': [6.5, 7.0, 7.0, 7.5, 7.8]
    })
    
    fig2 = px.line(progress_data, x='Date', y='Overall Score',
                   title='Progress Tracking')
    st.plotly_chart(fig2, use_container_width=True)