from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.callbacks.manager import get_openai_callback
import json
from typing import List, Dict, Tuple, Any
import numpy as np
import re
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

class IELTSEssayAnalyzer:
    def __init__(self, 
                 max_essay_length: int = 3000,
                 temperature: float = 0.4,
                 suggestion_temperature: float = 0.7,
                 verifier_temperature: float = 0.1,
                 model: str = "gpt-4o-mini"):
        self.max_essay_length = max_essay_length
        self.llm = ChatOpenAI(openai_api_key=api_key, model=model, temperature=temperature)
        self.suggestions_llm = ChatOpenAI(openai_api_key=api_key, model=model, 
                                    temperature=suggestion_temperature)
        self.verifier_llm = ChatOpenAI(openai_api_key=api_key, model=model, temperature=verifier_temperature)
        
        self.valid_scores = np.arange(0, 9.5, 0.5).tolist()
        

        self.prompt = '''You are an AI IELTS essay evaluator. Your task is to analyze the essay provided below based on four IELTS scoring criteria: **Task Response**, **Coherence and Cohesion**, **Lexical Resource**, and **Grammatical Range and Accuracy**. 

        For each criterion:
        1. **Provide a Band Score**: Assign a band score (in 0.5 increments, e.g., 5.0, 5.5, 6.0, up to 9.0) based on the IELTS band descriptors. 
        2. **Highlight Strengths**: Identify and list positive aspects of the essay that contribute to the score under this criterion.
        3. **Identify Errors**: Provide a detailed analysis of errors, including their location (start and end character positions), the problematic text, and an explanation of why it is considered an error. Explain the reasoning behind error identification.
        4. **Explain the Score**: Offer detailed reasoning for the assigned score by explaining how the essay meets or falls short of the scoring descriptors.

        Your output must conform strictly to the following JSON format:

        ```json
        {{
            "results": [
                {{
                    "Name": "<Criterion Name>",
                    "Score": <numerical score>,
                    "Reasoning for Score": "<string>",
                    "Strengths": ["<list of strengths>"],
                    "Errors": [
                        {{
                            "start": <int>,
                            "end": <int>,
                            "error_text": "<string>",
                            "description": "<string>",
                            "Reasoning for Error Identification": "<string>"
                        }}
                    ]
                }}
            ]
        }}

        Criterion-Specific Evaluation Guidelines

        1. Task Response:

        Evaluate the relevance, completeness, and development of ideas in response to the topic. Focus on:
            •	Strengths: Highlight well-developed arguments, relevant examples, and clear focus on all parts of the task.
            •	Errors: Identify issues such as irrelevant information, underdeveloped arguments, unsupported claims, or failure to address all parts of the question.

        2. Coherence and Cohesion:

        Assess the logical flow of ideas, use of cohesive devices, and paragraphing. Focus on:
            •	Strengths: Highlight logical progression of ideas, effective paragraph structure, and appropriate use of cohesive devices.
            •	Errors: Identify issues like unclear organization, overuse/misuse of linking words, poor paragraphing, or abrupt transitions.

        3. Lexical Resource:

        Evaluate vocabulary range, precision, and appropriateness for the task. Focus on:
            •	Strengths: Highlight use of a wide range of precise vocabulary, effective paraphrasing, and appropriate collocations.
            •	Errors: Identify repetition, inappropriate word choices, spelling mistakes, or limited vocabulary.

        4. Grammatical Range and Accuracy:

        Evaluate the variety and accuracy of sentence structures, grammar, and punctuation. Focus on:
            •	Strengths: Highlight accurate use of complex structures, diverse sentence types, and correct punctuation.
            •	Errors: Identify grammar mistakes (e.g., tense, subject-verb agreement), sentence structure issues, or punctuation errors.
                
        Example JSON Output:
        {{
    "results": [
        {{
            "Name": "Task Response",
            "Score": 7.0,
            "Reasoning for Score": "The essay addresses both parts of the task, presenting relevant examples and a clear focus. However, some ideas are underdeveloped, and there is minor repetition of arguments.",
            "Strengths": ["Addresses both parts of the task", "Provides relevant examples", "Clear topic focus"],
            "Errors": [
                {{
                    "start": 100,
                    "end": 120,
                    "error_text": "This is evident in many places.",
                    "description": "Underdeveloped idea: The statement lacks detailed explanation or support.",
                    "Reasoning for Error Identification": "The argument is vague and does not expand on how or why it is evident."
                }}
            ]
        }},
        {{
            "Name": "Coherence and Cohesion",
            "Score": 6.5,
            "Reasoning for Score": "The essay generally organizes information logically and uses cohesive devices effectively, but there are instances of overusing transition words and unclear topic sentences.",
            "Strengths": ["Logical flow of ideas", "Appropriate use of cohesive devices in most parts"],
            "Errors": [
                {{
                    "start": 200,
                    "end": 220,
                    "error_text": "However, it is also important.",
                    "description": "Overuse of transition words: 'However' is not needed here and disrupts the flow.",
                    "Reasoning for Error Identification": "The transition word does not logically connect the preceding and following ideas."
                }}
            ]
        }}
    ]
}}

    Essay:
    {essay}
    Topic:
    {topic}'''

        self.suggestions_prompt = """Based on the following errors found in an IELTS essay for the criterion '{criterion}':
                       {errors}
                       Provide specific suggestions for improvement. 
                        You MUST respond ONLY with valid JSON. Do NOT include any explanatory text, commentary, or any other output outside of the JSON structure defined below.
                       {{
                         "suggestions": [
                           {{
                             "error_text": <the problematic text>,
                             "suggestion": <detailed suggestion for improvement>,
                             "example": <specific example of correct usage>
                           }}
                         ],
                         "general_advice": [<list of general improvement tips>],
                         "recommended_exercises": [<list of specific practice exercises>]
                       }}"""

    def _validate_score(self, score: float) -> float:
        if not isinstance(score, (int, float)):
            return 0.0
        if score < 0:
            return 0.0
        if score > 9.0:
            return 9.0
        closest_score = min(self.valid_scores, key=lambda x: abs(x - score))
        return closest_score

    def _generate_suggestions(self, errors: List[Dict], criterion: str) -> Dict:
        if not errors:
            return {
                "suggestions": [],
                "general_advice": ["Continue practicing to maintain current level"],
                "recommended_exercises": ["Regular writing practice"]
            }

        formatted_errors = "\n".join(
            f"- {error['error_text']}: {error['description']}"
            for error in errors
        )
        try:
            result = self.suggestions_llm([SystemMessage(content='You are a professional IELTS errors checker'), HumanMessage(content=self.suggestions_prompt.format(errors=formatted_errors, criterion=criterion))])
            suggestions_data = json.loads(result.content)
            return {
                    "suggestions": suggestions_data.get('suggestions', []),
                    "general_advice": suggestions_data.get('general_advice', []),
                    "recommended_exercises": suggestions_data.get('recommended_exercises', [])
                }
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return {
                "suggestions": [],
                "general_advice": ["Error generating specific suggestions"],
                "recommended_exercises": []
            }
    
    def _create_verifier_prompt(self, evaluator_json: dict, essay: str, topic: str) -> str:
        verifier_prompt_template = """You are an AI assistant tasked with verifying the output of an IELTS essay evaluation. You will receive a JSON object containing the evaluation of an essay across four criteria: Task Response, Coherence and Cohesion, Lexical Resource, and Grammatical Range & Accuracy.

        Your task is to meticulously check the evaluation for the following:
        0. Check if the essay text and topic match the provided input. If they do not match, flag this as an error and assign score for Task Response 0.0.
        1. Correctness of Scores: Do the assigned scores align with the provided reasoning and the IELTS band descriptors? Are there any scores that seem too high or too low based on the identified errors and the scoring guidelines?
        2. Completeness of Error Detection: Has the Evaluator identified all instances of the specified error types for each criterion? Are there any obvious errors that have been missed? Are there any additional errors that should be included? Check the essay text below line by line to verify the accuracy of error identification.
        3. Correctness of Categorization: Are all identified errors assigned to the correct criterion? Are there any errors that have been incorrectly categorized (e.g., a grammatical error assigned to Task Response or other criterion)?
        4. Consistency of Reasoning: Does the reasoning provided for scores and errors logically align with the scoring guidelines and the specific criteria? Are there any contradictions or inconsistencies in the reasoning?
        5. Accuracy of Error Reporting: Are the 'start' and 'end' character positions correct for each identified error? Is the 'error_text' the exact text containing the error? Are the error descriptions clear and accurate?

        For each identified error or inconsistency, BEFORE making any changes, explain your reasoning in the JSON with following format:
        "Verifier's Comments": "[Your detailed reasoning here]"

        Then, provide the corrected JSON object. The output must be a valid JSON with "results" and "Verifier's Comments" keys. If you dont find any errors the "Verifier's Comments" should be an empty string.

        You MUST Return ONLY the corrected JSON object with the following structure:

        Example Correction (Missing Reasoning for Error):
        Original JSON:
        {{
            "results": [{{
                "Name": "Lexical Resource",
                "Score": 7.0,
                "Errors": [{{
                    "start": 10,
                    "end": 15,
                    "error_text": "runing",
                    "description": "Spelling error"
                }}]
            }}]
        }}
        Corrected JSON:
        {{
            "results": [{{
                "Name": "Lexical Resource",
                "Score": 7.0,
                "Errors": [{{
                    "start": 10,
                    "end": 15,
                    "error_text": "runing",
                    "description": "Spelling error: should be 'running'",
                    "Reasoning for Error Identification": "The word 'runing' is misspelled. The correct spelling is 'running'."
                }}]
            }}],
            "Verifier's Comments": "The error description is missing for the spelling error in the Lexical Resource criterion."
        }}

        This is EXTREMELY important for me, and if you do a great job, I will reward you with a bonus! Good luck!
        Before returning the corrected JSON, check it again to ensure accuracy and completeness.

        Here is the JSON you need to verify with the essay text and topic:
        {evaluator_json_str}\n
        {topic}\n
        {essay}
        """

        evaluator_json_str = json.dump(evaluator_json, indent=4)
        return verifier_prompt_template.format(evaluator_json_str=evaluator_json_str, essay=essay, topic=topic)

    def _parse_json(self, generated_text: str) -> dict:
        generated_text = generated_text.strip()
        try:
            return json.loads(generated_text)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            generated_text = generated_text.replace("```json", "").replace("```", "")
            try:
                return json.loads(generated_text)
            except:
                print("JSON could not be fixed: {generated_text}")
                return None
    
    def _process_results(self, parsed_result: dict) -> List[Dict[str, Any]]:
        results = []
        for item in parsed_result.get("results", []):
            errors = []
            for error in item.get('Errors', []):
                try:
                    error_text = error.get('error_text', "")
                    errors.append({**error, 'error_text': error_text})
                except (KeyError, IndexError) as e:
                    print(f"Error processing error entry: {e}")
                    continue
            suggestions_data = self._generate_suggestions(errors, item['Name'])
            validated_score = self._validate_score(float(item.get('Score',0)))
            strength = item.get('Strengths', [])
            results.append({
                'Name': item['Name'],
                'Score': validated_score,
                'Errors': errors,
                'Strengths': strength,
                'Suggestions': suggestions_data['suggestions'],
                'GeneralAdvice': suggestions_data['general_advice'],
                'Exercises': suggestions_data['recommended_exercises']
            })
        return results
    
    def _process_errors(self, parsed_result: dict) -> List[Dict[str, Any]]:
        all_errors = []
        for item in parsed_result.get("results", []):
                errors = [{**error, 'Name': item['Name'], 'Criterion': item['Name']} for error in item.get('Errors', [])]
                all_errors.extend(errors)
        return all_errors
        
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injections or harmful content."""
        text = re.sub(r'[<>{}\[\];]', '', text)
        text = re.sub(r'[^\x20-\x7E\n]', '', text) 
        return text[:3000]

    def analyze_essay(self, essay_text: str, topic: str) -> Tuple[List[Dict], List[Dict]]:
        print("Analyzing essay...")

        essay_text = self.sanitize_input(essay_text)

        try:
            with get_openai_callback() as cb:
                evaluator_result = self.llm.invoke([SystemMessage(content="You are an AI IELTS essay evaluator. Your task is to analyze the essay provided below based on four IELTS scoring criteria: **Task Response**, **Coherence and Cohesion**, **Lexical Resource**, and **Grammatical Range and Accuracy**."), 
                                                    HumanMessage(content=self.prompt.format(essay=essay_text, topic=topic))])
                #print(f"Evaluator OpenAI Callback: {cb}")

            evaluator_json = self._parse_json(evaluator_result.content)
            if not evaluator_json:
                return [], []

            verifier_prompt = self._create_verifier_prompt(evaluator_json, essay_text, topic)

            with get_openai_callback() as cb:
                verifier_result = self.verifier_llm.invoke([SystemMessage(content="You are an AI assistant tasked with verifying the output of an IELTS essay evaluation. You will receive a JSON object containing the evaluation of an essay across four criteria: Task Response, Coherence and Cohesion, Lexical Resource, and Grammatical Range & Accuracy."), 
                                                          HumanMessage(content=verifier_prompt)])
                #print(f"Verifier OpenAI Callback: {cb}")

            verifier_json = self._parse_json(verifier_result.content)

            if not verifier_json:
                print("Verifier JSON could not be parsed, using evaluator results")
                return self._process_results(evaluator_json), self._process_errors(evaluator_json)
            
            verifier_comments = verifier_json.pop("Verifier's Comments", "")
            print(f"Verifier comments:\n{verifier_comments}")

            return self._process_results(verifier_json), self._process_errors(verifier_json)

        except Exception as e:
            print(f"An error occurred: {e}")
            return [], []

