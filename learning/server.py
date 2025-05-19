import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExamRequest(BaseModel):
    topic: str

class Subtopic(BaseModel):
    name: str
    answers: List[bool]

class responseData(BaseModel):
    mainTopic: str
    subtopics: List[Subtopic]

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
# GEMINI_API_KEY = "AIzaSyAkJymSAbYFO_j4ZYA_voTGOvuel_wgok4"

import json

def call_gemini_api(prompt: str):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    try:
        text_response = response.json()['candidates'][0]['content']['parts'][0]['text']

        # Remove ```json and ``` wrapping
        if text_response.startswith("```json"):
            text_response = text_response.strip("```json").strip()
        if text_response.startswith("```"):
            text_response = text_response.strip("```").strip()

        # Convert the JSON string into a real Python object
        parsed_data = json.loads(text_response)
        return parsed_data

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Error parsing Gemini API response: {str(e)}")

@app.post("/create_exam")
async def create_exam(request: ExamRequest):
    question_content = f"""
        Create a short exam with exactly 10 multiple-choice questions on the topic: {request.topic}.
        The content of the questions should be subtopics of {request.topic} and even subtopics of the subtopic.
        The response to my prompt should be in the following format:

        {{
            "exam1": {{
                "question_statement": "Place your question here",
                "options": ["Option A", "Option B", "Option C", "Option D"]
            }},
            "answer1": {{
                "question_statement": "Correct answer"
            }},
            "subtopic1": {{
                "question_statement": "Relevant subtopic of the question"
            }}
        }}

        For example:

        {{
            "exam1": {{
                "question_statement": "What was the primary cause of World War II?",
                "options": ["Option A: Political Tensions", "Option B: Economic Crisis", "Option C: Assassination of a key figure", "Option D: Natural Disaster"]
            }},
            "answer1": {{
                "question_statement": "Option A: Political Tensions"
            }},
            "subtopic1": {{
                "question_statement": "World War II Causes"
            }}
        }}
    """
    exam_response = call_gemini_api(question_content)
    return {"exam": exam_response}

@app.post("/generate_learning_tree")
async def generate_learning_tree(request: responseData):
    main_topic = request.mainTopic
    subtopics = [subtopic.name for subtopic in request.subtopics]
    formatted_subtopics = ', '.join([f"'{sub}'" for sub in subtopics])

    question_content = f"""
    Create a tree structure for the main topic of {main_topic} with a minimum depth of 3 levels.
    Under the main topic, include the following categories and the overarching categories as provided:
    {formatted_subtopics}.
    The output format must be in json format as follows:
    {{name: mainTopicName, children: [{{name: subtopic1, children: [{{name: subsubtopic1}}, {{name: subsubtopic2}}]}}]}}
    """
    tree_response = call_gemini_api(question_content)
    return {"tree": tree_response}

def create_node():
    pass

def create_tree():
    pass

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)




