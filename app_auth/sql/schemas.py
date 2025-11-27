from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime

class Message(BaseModel):
    detail: Optional[str] = Field(example="error or success message")

class HealthResponse(BaseModel):
    detail: str = Field(example="OK")
    replica: str = Field(example="compose-repo-auth-1")
    ip: str = Field(example="172.18.0.5")

class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role_id: int


class UserResponse(UserBase):
    id: int
    role_id: int
    model_config = ConfigDict(from_attributes=True)
    
class UserUpdate(UserResponse):
    pass

class RefreshRequest(BaseModel):
    refresh_token_str: str

class RefreshTokenBase(BaseModel):
    token: str
    expires_at: datetime
    revoked: bool = Field(default=False)


class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str
    expires_at: datetime


class RefreshTokenResponse(RefreshTokenBase):
    id: int
    user_id: int
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)