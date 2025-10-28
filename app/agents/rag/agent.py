# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from dotenv import load_dotenv
from .prompts import RAG_AGENT_INSTRUCTIONS

load_dotenv()

rag_corpus_config = {
    "adn-chn-cicd": "projects/1017255190337/locations/europe-west1/ragCorpora/2305843009213693952",
    "adn-chn-staging": "projects/744316316183/locations/europe-west1/ragCorpora/5764607523034234880",
    "adn-chn-prod": "projects/193014075033/locations/europe-west1/ragCorpora/4611686018427387904",
}

def get_rag_corpus(project_id):
    return rag_corpus_config.get(project_id, rag_corpus_config["adn-chn-cicd"])
    
_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

rag_corpus = get_rag_corpus(project_id)

# Build tools list conditionally based on RAG_CORPUS availability
tools = []

if rag_corpus:
    ask_vertex_retrieval = VertexAiRagRetrieval(
        name='retrieve_rag_documentation',
        description=(
            'Use this tool to retrieve documentation and reference materials for the question from the RAG corpus,'
        ),
        rag_resources=[
            rag.RagResource(
                # please fill in your own rag corpus
                # here is a sample rag corpus for testing purpose
                # e.g. projects/123/locations/us-central1/ragCorpora/456
                rag_corpus=rag_corpus
            )
        ],
        similarity_top_k=10,
        vector_distance_threshold=0.6,
    )
    tools.append(ask_vertex_retrieval)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='ask_rag_agent',
    instruction=RAG_AGENT_INSTRUCTIONS,
    tools=tools,
)