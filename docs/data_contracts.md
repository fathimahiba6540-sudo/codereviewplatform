# Backend to Frontend Data Contracts

## 1. Authentication Contracts

### POST `/api/v1/auth/register`
**Request**:
```json
{
  "email": "user@example.com",
  "username": "developer",
  "password": "SecurePassword123!"
}
```
**Response (201 Created)**:
```json
{
  "id": "usr_12345",
  "email": "user@example.com",
  "username": "developer",
  "created_at": "2026-08-03T20:44:00Z"
}
```

### POST `/api/v1/auth/login`
**Request**:
```json
{
  "username": "developer",
  "password": "SecurePassword123!"
}
```
**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 691200
}
```

---

## 2. Project & Upload Contracts

### POST `/api/v1/projects/upload` (Multipart Form)
- `file`: `.zip` archive file binary
- `title`: string optional

**Response (202 Accepted)**:
```json
{
  "project_id": "prj_98765",
  "status": "INGESTING",
  "filename": "repo.zip",
  "file_count": 42,
  "languages": ["Python", "JavaScript", "Dart"]
}
```

---

## 3. Review Report Contract

### GET `/api/v1/reviews/{review_id}`
**Response (200 OK)**:
```json
{
  "review_id": "rev_55512",
  "project_id": "prj_98765",
  "overall_score": 85.5,
  "grade": "A",
  "summary": "The codebase exhibits high overall quality with minor security concerns in environment variable handling.",
  "scores": {
    "maintainability": 88.0,
    "security": 78.0,
    "performance": 90.0,
    "readability": 86.0
  },
  "findings": {
    "bugs": [],
    "security_vulnerabilities": [
      {
        "file": "backend/app/core/config.py",
        "line": 15,
        "severity": "MEDIUM",
        "issue": "Hardcoded secret fallback string detected in dev settings."
      }
    ],
    "code_smells": []
  },
  "documentation": {
    "overview": "FastAPI & Flutter Architecture",
    "setup_steps": ["pip install -r requirements.txt", "uvicorn backend.app.main:app"]
  },
  "generated_tests": [
    {
      "target_file": "backend/app/routers/health.py",
      "test_code": "def test_health(): assert response.status_code == 200"
    }
  ]
}
```
