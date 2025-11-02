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
import uuid
import random

from locust import HttpUser, between, task


class ChatStreamUser(HttpUser):
    """Simulates a user interacting with the Clinical Agent API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    # Liste de questions médicales pour varier les tests
    MEDICAL_QUERIES = [
        "Bonjour! Quels sont les symptômes d'un AVC?",
        "Comment reconnaître un arrêt cardiaque?",
        "Que faire en cas d'hémorragie importante?",
        "Quels sont les signes d'une intoxication médicamenteuse?",
        "Comment identifier une crise d'asthme sévère?",
        "Quels sont les symptômes d'une allergie grave?",
        "Comment réagir face à une convulsion?",
        "Quels sont les signes d'un infarctus du myocarde?",
    ]

    @task(3)
    def chat_stream(self) -> None:
        """Simulates a complete chat interaction (session + message)."""
        headers = {"Content-Type": "application/json"}
        if os.environ.get("_ID_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['_ID_TOKEN']}"
        
        # Create session using custom endpoint
        user_id = f"user_{uuid.uuid4()}"
        
        # Créer la session - Locust track automatiquement
        with self.client.post(
            "/start_session",
            headers=headers,
            json={"user_id": user_id},
            catch_response=True,
            name="POST /start_session",
        ) as session_response:
            if session_response.status_code != 200:
                session_response.failure(
                    f"Session creation failed: {session_response.status_code}"
                )
                return
            
            try:
                session_data = session_response.json()
                session_id = session_data["session_id"]
                session_response.success()
            except (KeyError, ValueError) as e:
                session_response.failure(f"Invalid session response: {str(e)}")
                return

        # Send chat message - Locust track automatiquement
        message_data = {
            "user_id": user_id,
            "session_id": session_id,
            "query": random.choice(self.MEDICAL_QUERIES),
        }

        with self.client.post(
            "/send_message",
            name="POST /send_message",
            headers=headers,
            json=message_data,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Vérifier que la réponse contient bien une réponse de l'agent
                    if response_data.get("success") and response_data.get("response"):
                        response.success()
                    else:
                        response.failure("Response missing agent reply")
                        
                except Exception as e:
                    response.failure(f"Failed to parse response: {str(e)}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_session_state(self) -> None:
        """Test the get_state endpoint."""
        headers = {"Content-Type": "application/json"}
        if os.environ.get("_ID_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['_ID_TOKEN']}"
        
        user_id = f"user_{uuid.uuid4()}"
        
        # Créer d'abord une session
        with self.client.post(
            "/start_session",
            headers=headers,
            json={"user_id": user_id},
            catch_response=True,
            name="POST /start_session (state)",
        ) as session_response:
            if session_response.status_code != 200:
                return
            
            try:
                session_data = session_response.json()
                session_id = session_data["session_id"]
                session_response.success()
            except (KeyError, ValueError):
                return

        # Récupérer l'état de la session
        with self.client.post(
            "/get_state",
            headers=headers,
            json={"user_id": user_id, "session_id": session_id},
            catch_response=True,
            name="POST /get_state",
        ) as response:
            if response.status_code == 200:
                try:
                    state_data = response.json()
                    if state_data.get("success"):
                        response.success()
                    else:
                        response.failure("State retrieval unsuccessful")
                except Exception as e:
                    response.failure(f"Failed to parse state: {str(e)}")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_agent_outputs(self) -> None:
        """Test the get_agent_outputs endpoint."""
        headers = {"Content-Type": "application/json"}
        if os.environ.get("_ID_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['_ID_TOKEN']}"
        
        user_id = f"user_{uuid.uuid4()}"
        
        # Créer d'abord une session
        with self.client.post(
            "/start_session",
            headers=headers,
            json={"user_id": user_id},
            catch_response=True,
            name="POST /start_session (outputs)",
        ) as session_response:
            if session_response.status_code != 200:
                return
            
            try:
                session_data = session_response.json()
                session_id = session_data["session_id"]
                session_response.success()
            except (KeyError, ValueError):
                return

        # Récupérer les outputs des agents
        with self.client.post(
            "/get_agent_outputs",
            headers=headers,
            json={"user_id": user_id, "session_id": session_id},
            catch_response=True,
            name="POST /get_agent_outputs",
        ) as response:
            if response.status_code == 200:
                try:
                    outputs_data = response.json()
                    if outputs_data.get("success"):
                        response.success()
                    else:
                        response.failure("Outputs retrieval unsuccessful")
                except Exception as e:
                    response.failure(f"Failed to parse outputs: {str(e)}")
            else:
                response.failure(f"Status code: {response.status_code}")