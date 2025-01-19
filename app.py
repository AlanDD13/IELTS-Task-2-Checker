import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from essay_analyzer import IELTSEssayAnalyzer
from html import escape
from bs4 import BeautifulSoup
from pprint import pprint

st.set_page_config(
    page_title="IELTS Essay Analyzer",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={'About': "# IELTS Essay Analyzer"}
)

st.markdown("""
    <style>
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
        width: 300px;
        background-color: #333;
        color: white;
        text-align: left;
        padding: 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .error-highlight:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }

    .suggestion-box {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }

    .error-text {
        color: #d32f2f;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def highlight_text_with_errors(text: str, errors: list[dict]) -> str:
    highlighted_text = escape(text)
    offset = 0

    for error in errors:
        error_text = error['error_text']
        start = text.find(error_text) 
        if start == -1:
            print(f'Error text "{error_text}" not found in the text')
            continue  

        end = start + len(error_text)

        highlight_html = f'<span class="error-highlight"> {error_text} <span class="tooltip-text"> <b style=\'align: center;\'>{error["description"]}</b> </span> </span>'
        highlighted_text = highlighted_text[:start] + highlight_html + highlighted_text[end:]
        offset += len(highlight_html) - len(error_text)
        #print(f'Error: {error_text}, start: {start}, end: {end}, offset: {offset}')
    return f'<div>{highlighted_text}</div>'

analyzer = IELTSEssayAnalyzer()

st.title("IELTS Essay Analyzer")

main_col = st.container()
sidebar = st.sidebar

with main_col:
    essay_topic = st.text_input("Essay Topic")
    essay_text = st.text_area("Enter your essay here", height=300)
    
    if st.button("Analyze Essay"):
        if essay_text and essay_topic:
            with st.spinner("Analyzing your essay..."):
                scores, errors = analyzer.analyze_essay(essay_text, essay_topic)
                
                st.session_state['scores'] = scores
                st.session_state['errors'] = errors
                
                if len(scores) > 0:
                    overall_score = sum(score['Score'] for score in scores) / len(scores)
                    overall_score = round(overall_score * 2) / 2 
                    
                    st.markdown("### Overall Score")
                    st.write(f"**{overall_score:.1f}**")
                    
                    for score in scores:
                        st.write(f"**{score['Name']}**: {score['Score']:.1f}")

                    st.markdown("### Your Essay with Annotations")
                    highlighted_text = highlight_text_with_errors(essay_text, errors)

                    soup = BeautifulSoup(highlighted_text, 'html.parser')
                    clean_html = str(soup)

                    st.write(clean_html, unsafe_allow_html=True)
                    
                    st.markdown("### Detailed Analysis")
                    #pprint(scores)
                    #pprint(scores)
                    for score in scores:
                        with st.expander(f"**{score['Name']}** ({score['Score']:.1f}/9.0)"):
                            if score['Errors']:
                                st.write('**Identified Issues:**')
                                for error in score['Errors']:
                                    st.markdown(f"""
                                        <div class='error-box'>
                                            <p><span class='error-text'>Error text:</span> "{error['error_text']}"</p>
                                            <p><span class='error-text'>Issue:</span> {error['description']}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                            
                            if score['Strengths']:
                                st.write("**Strengths:**")
                                for strength in score['Strengths']:
                                    st.markdown(f"""
                                        <div class='suggestion-box'>
                                            <p><b>Strength:</b> {strength}</p>
                                        </div>
                                    """, unsafe_allow_html=True)

                            if score['Suggestions']:
                                st.write("**Specific Improvements:**")
                                for suggestion in score['Suggestions']:
                                    st.markdown(f"""
                                        <div class='suggestion-box'>
                                            <p><b>Problem:</b> {suggestion['error_text']}</p>
                                            <p><b>Suggestion:</b> {suggestion['suggestion']}</p>
                                            <p><b>Example:</b> {suggestion['example']}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                            
                            if score['GeneralAdvice']:
                                st.write("**General Advice:**")
                                for advice in score['GeneralAdvice']:
                                    st.markdown(f"""
                                        <div class='suggestion-box'>
                                            {advice}
                                        </div>
                                    """, unsafe_allow_html=True)
                            
                            if score['Exercises']:
                                st.write("**Recommended Exercises:**")
                                for exercise in score['Exercises']:
                                    st.markdown(f"""
                                        <div class='suggestion-box'>
                                            {exercise}
                                        </div>
                                    """, unsafe_allow_html=True)


with sidebar:
    st.markdown("### IELTS Scores")
    if 'scores' in st.session_state and len(st.session_state['scores']) > 0:
        scores = st.session_state['scores']
        
        score_df = pd.DataFrame({
            'Criterion': [score['Name'] for score in scores],
            'Score': [score['Score'] for score in scores]
        })
        
        fig = px.bar(score_df, x='Criterion', y='Score',
                    range_y=[0, 9],
                    title='IELTS Assessment')
        
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                ticktext=[str(i/2) for i in range(0, 19)],
                tickvals=[i/2 for i in range(0, 19)],
                gridcolor='rgba(0,0,0,0.1)',
                zeroline=True,
                zerolinecolor='rgba(0,0,0,0.2)'
            ),
            plot_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Error Analysis")
        if 'errors' in st.session_state:
            errors = st.session_state['errors']
            error_counts = pd.DataFrame({
                'Criterion': [error['Criterion'] for error in errors]
            }).value_counts().reset_index()
            error_counts.columns = ['Criterion', 'Number of Errors']
            
            fig_errors = px.pie(error_counts, names='Criterion', values='Number of Errors',
                              title='Distribution of Errors by Criterion')
            st.plotly_chart(fig_errors, use_container_width=True)
        
        st.markdown("### Progress Tracking")

        if 'progress_data' not in st.session_state:
            st.session_state['progress_data'] = pd.DataFrame({
                'Date': [datetime.now()],
                'Overall Score': [sum(score['Score'] for score in scores) / len(scores)],
                'Task Response': [next((s['Score'] for s in scores if s['Name'] == 'Task Response'), None)],
                'Coherence and Cohesion': [next((s['Score'] for s in scores if s['Name'] == 'Coherence and Cohesion'), None)],
                'Lexical Resource': [next((s['Score'] for s in scores if s['Name'] == 'Lexical Resource'), None)],
                'Grammar': [next((s['Score'] for s in scores if s['Name'] == 'Grammatical Range & Accuracy'), None)]
            })
        else:
            new_data = pd.DataFrame({
                'Date': [datetime.now()],
                'Overall Score': [sum(score['Score'] for score in scores) / len(scores)],
                'Task Response': [next((s['Score'] for s in scores if s['Name'] == 'Task Response'), None)],
                'Coherence and Cohesion': [next((s['Score'] for s in scores if s['Name'] == 'Coherence and Cohesion'), None)],
                'Lexical Resource': [next((s['Score'] for s in scores if s['Name'] == 'Lexical Resource'), None)],
                'Grammar': [next((s['Score'] for s in scores if s['Name'] == 'Grammatical Range & Accuracy'), None)]
            })
            st.session_state['progress_data'] = pd.concat([st.session_state['progress_data'], new_data], ignore_index=True)

        progress_data = st.session_state['progress_data']

        cols_to_numeric = ['Overall Score', 'Task Response', 'Coherence and Cohesion', 'Lexical Resource', 'Grammar']
        for col in cols_to_numeric:
            progress_data[col] = pd.to_numeric(progress_data[col], errors='coerce')

        fig_progress = px.line(progress_data, x='Date', y='Overall Score',
                             title='Overall Score Progress',
                             labels={'Overall Score': 'IELTS Score'},
                             markers=True)

        fig_progress.update_layout(
            yaxis=dict(
                tickmode='array',
                ticktext=[str(i/2) for i in range(0, 19)],
                tickvals=[i/2 for i in range(0, 19)],
                range=[0, 9]
            )
        )
        st.plotly_chart(fig_progress, use_container_width=True)

        progress_data_melted = progress_data.melt(id_vars=['Date'],
                                                  value_vars=['Task Response', 'Coherence and Cohesion', 'Lexical Resource', 'Grammar'],
                                                  var_name='Criterion', value_name='Score')

        criterion_progress = px.line(
            progress_data_melted,
            x='Date',
            y='Score',
            color='Criterion',
            title='Progress by Criterion',
            labels={'Score': 'Score'},
            markers=True
        )

        criterion_progress.update_layout(
            yaxis=dict(
                tickmode='array',
                ticktext=[str(i/2) for i in range(0, 19)],
                tickvals=[i/2 for i in range(0, 19)],
                range=[0, 9]
            )
        )
        st.plotly_chart(criterion_progress, use_container_width=True)

        if st.button("Export Analysis Report"):
            report = pd.DataFrame({
                'Criterion': [score['Name'] for score in scores],
                'Score': [score['Score'] for score in scores],
                'Errors': [score['Errors'] for score in scores],
                'Suggestions': [score['Suggestions'] for score in scores]
            })
            
            st.download_button(
                label="Download Report",
                data=report.to_csv(index=False),
                file_name=f"ielts_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
