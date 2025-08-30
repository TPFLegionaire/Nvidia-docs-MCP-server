from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DocumentBase(BaseModel):
    product_type: str = Field(..., description="Type of NVIDIA product")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    url: str = Field(..., description="Source URL")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}