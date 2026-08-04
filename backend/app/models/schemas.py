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
