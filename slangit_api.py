import requests
import os
from typing import Dict, List, Optional
import json

class SlangitAPI:
    def __init__(self, base_url: str, token: str, space_id: int):
        self.base_url = base_url
        self.token = token
        self.space_id = space_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        response = requests.post(
            f"{self.base_url}/v1/create-conversation",
            headers=self.headers,
            json={"spaceId": self.space_id}
        )
        response.raise_for_status()
        return response.json()["conversation"]["id"]

    def send_message(self, conversation_id: str, message: str) -> str:
        """Send a message to a conversation and return the response"""
        response = requests.post(
            f"{self.base_url}/v1/send-message",
            headers=self.headers,
            json={
                "message": message,
                "file": None,
                "messageType": "TEXT",
                "conversationId": conversation_id,
                "language": "EN"
            },
            stream=True
        )
        response.raise_for_status()

        full_response = ""
        for chunk in response.iter_lines():
            if chunk:
                decoded_chunk = chunk.decode('utf-8').replace('data: ', '')
                try:
                    chunk_json = json.loads(decoded_chunk)
                    full_response = chunk_json.get('messageText', full_response)
                except json.JSONDecodeError:
                    continue
        return full_response

    def batch_process_questions(self, questions: List[str]) -> List[Dict]:
        """Process a batch of questions for the current space"""
        conversation_id = self.create_conversation()
        results = []
        
        for question in questions:
            try:
                answer = self.send_message(conversation_id, question)
                status = "success"
                if ("sorry" in answer.lower()):
                    status = "error"

                results.append({
                    "question": question,
                    "answer": answer,
                    "status": status
                })
            except Exception as e:
                results.append({
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "status": "error"
                })
        
        return results

class MultiSpaceProcessor:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.output_dir = "space_query_results"
        os.makedirs(self.output_dir, exist_ok=True)

    def process_spaces(self, space_ids: List[int], questions: List[str]) -> Dict[str, List[Dict]]:
        """Process multiple spaces with the same set of questions"""
        results = {}
        
        for space_id in space_ids:
            try:
                api = SlangitAPI(self.base_url, self.token, space_id)
                space_results = api.batch_process_questions(questions)
                results[str(space_id)] = space_results
            except Exception as e:
                results[str(space_id)] = [{
                    "error": f"Failed to process space {space_id}: {str(e)}"
                }]
        
        return results

    def save_results(self, results: Dict[str, List[Dict]], filename_prefix: str = "batch_results") -> str:
        """Save results to a JSON file and return the file path"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        return filepath
