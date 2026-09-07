import sys
import os
import requests

API_URL = os.getenv("AI_REVIEW_API_URL", "http://localhost:8000/api/v1")


def trigger_workspace_review(project_id: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/projects/{project_id}/review", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ai_review_client.py <PROJECT_ID> <JWT_TOKEN>")
        sys.exit(1)
    trigger_workspace_review(sys.argv[1], sys.argv[2])
