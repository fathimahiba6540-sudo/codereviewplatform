from datetime import datetime
from typing import List, Optional, Generic, TypeVar, Any
from pydantic import BaseModel, EmailStr, HttpUrl, Field

T = TypeVar("T")


# API Response Wrapper Envelopes
class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Auth Schemas
class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# Project & Repository Import Schemas
class GitHubImportRequest(BaseModel):
    github_url: str = Field(..., example="https://github.com/fastapi/fastapi")
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    github_token: Optional[str] = Field(None, description="Optional GitHub Personal Access Token for private repositories")


class FileResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_path: str
    language: str
    file_size_bytes: int
    line_count: int
    content_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    source_type: str
    github_url: Optional[str] = None
    status: str
    total_files: int
    total_lines_of_code: int
    detected_languages: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectSummaryResponse(BaseModel):
    project: ProjectResponse
    framework: str = "Generic"
    file_count: int
    lines_of_code: int
    languages: List[str]
    recent_files: List[FileResponse] = []
    latest_review: Optional[dict] = None


# Phase 4: Ingestion schemas
class IngestionStatusResponse(BaseModel):
    project_id: str
    status: str
    is_vectorized: bool
    total_files: int
    total_chunks: int
    framework: Optional[str] = None
    detected_languages: List[str] = []
    ingestion_error: Optional[str] = None


class FileBreakdownItem(BaseModel):
    id: str
    filename: str
    file_path: str
    language: str
    line_count: int
    file_size_bytes: int


class ProjectFilesSummaryResponse(BaseModel):
    project_id: str
    title: str
    framework: Optional[str] = None
    total_files: int
    total_lines_of_code: int
    total_chunks: int
    is_vectorized: bool
    status: str
    language_distribution: dict
    files: List[FileBreakdownItem] = []


class ChunkMetadata(BaseModel):
    """Metadata attached to each vectorized code chunk — used by AI agents in Phase 5."""
    chunk_id: str
    project_id: str
    file_id: Optional[str] = None
    file_path: str
    language: str
    chunk_index: int
    line_start: int
    line_end: int
    chunk_type: str
    node_name: Optional[str] = None
    node_type: Optional[str] = None


# New Feature Schemas: Title-Only Project, Error Solver, Code Generator, PDF Exam Summarizer
class TitleOnlyProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    language: Optional[str] = Field("python", description="Target programming language or tech stack")


class ErrorSolverRequest(BaseModel):
    code: str = Field(..., description="Source code to analyze for bugs and errors")
    error_log: Optional[str] = Field(None, description="Optional error log or exception stack trace")
    language: Optional[str] = Field("python", description="Programming language of the snippet")


class ErrorSolverResponse(BaseModel):
    error_summary: str
    root_cause: str
    corrected_code: str
    explanation: str
    prevention_tips: List[str] = []


class CodeGeneratorRequest(BaseModel):
    prompt: str = Field(..., description="Requirement or description of code to generate")
    language: Optional[str] = Field("python", description="Target programming language")
    framework: Optional[str] = Field(None, description="Optional target framework (e.g. FastAPI, React, Flask)")
    title: Optional[str] = Field(None, description="Optional title if creating a project")


class CodeGeneratorResponse(BaseModel):
    title: str
    language: str
    generated_code: str
    explanation: str
    file_name: str


class PDFSummaryResponse(BaseModel):
    combined_title: str
    total_pdfs_processed: int
    total_pages: int
    executive_summary: str
    high_yield_topics: List[dict] = []
    definitions_and_formulas: List[dict] = []
    exam_questions: List[dict] = []
    cheatsheet_markdown: str
    bundle_id: Optional[str] = None


class DoubtRequest(BaseModel):
    query: str = Field(..., description="Student or teacher doubt or question")
    code_context: Optional[str] = Field(None, description="Optional code snippet attached to the question")
    chat_history: List[dict] = Field([], description="Previous conversation turns for context")


class DoubtResponse(BaseModel):
    answer: str
    key_takeaways: List[str] = []
    related_topics: List[str] = []



