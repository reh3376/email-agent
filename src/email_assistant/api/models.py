"""Pydantic models for API request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants
SAMPLE_DATETIME = "2025-08-27T12:00:00Z"  # Sample datetime for examples


class Category(BaseModel):
    """Email classification category."""
    
    id: int = Field(
        ..., 
        ge=0, 
        le=4,
        description="Category ID (0-4)",
        examples=[0]
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Category name",
        examples=["reviewed"]
    )
    labels: List[str] = Field(
        ...,
        min_items=1,
        description="Available labels for this category",
        examples=[["yes", "no"]]
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the category"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 0,
                    "name": "reviewed",
                    "labels": ["yes", "no"]
                },
                {
                    "id": 1,
                    "name": "type",
                    "labels": ["personal", "work", "newsletter", "marketing"]
                }
            ]
        }
    )


class Taxonomy(BaseModel):
    """Email classification taxonomy."""
    
    type: Literal["email_categories"] = Field(
        default="email_categories",
        description="Type identifier for taxonomy"
    )
    version: str = Field(
        ...,
        pattern="^v\\d+$",
        description="Version identifier (e.g., v2)",
        examples=["v2"]
    )
    categories: List[Category] = Field(
        ...,
        min_items=5,
        max_items=5,
        description="List of classification categories"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata",
        examples=[{
            "createdAt": SAMPLE_DATETIME,
            "updatedAt": SAMPLE_DATETIME,
            "author": "admin"
        }]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "email_categories",
                    "version": "v2",
                    "categories": [
                        {"id": 0, "name": "reviewed", "labels": ["yes", "no"]},
                        {"id": 1, "name": "type", "labels": ["personal", "work", "newsletter", "marketing", "transactional", "social", "spam"]},
                        {"id": 2, "name": "senderIdentity", "labels": ["known", "unknown", "service", "company", "automated"]},
                        {"id": 3, "name": "context", "labels": ["general", "project", "event", "financial", "health", "education", "travel"]},
                        {"id": 4, "name": "handler", "labels": ["read", "respond", "schedule", "file", "delete", "delegate"]}
                    ],
                    "metadata": {
                        "createdAt": SAMPLE_DATETIME,
                        "updatedAt": SAMPLE_DATETIME,
                        "author": "admin"
                    }
                }
            ]
        }
    )


class Condition(BaseModel):
    """Rule condition."""
    
    field: str
    operator: str = Field(..., pattern="^(exists|eq|in|lt|lte|gt|gte|regex)$")
    value: Any
    logic: str = Field("AND", pattern="^(AND|OR)$")


class Action(BaseModel):
    """Rule action."""
    
    type: str
    parameters: Optional[Dict[str, Any]] = None


class Rule(BaseModel):
    """Processing rule."""
    
    id: str = Field(..., pattern="^[a-zA-Z0-9_-]+$")
    name: str
    description: Optional[str] = None
    priority: int = Field(..., ge=1)
    enabled: bool = True
    conditions: List[Condition]
    actions: List[Action]


class Ruleset(BaseModel):
    """Email processing ruleset."""
    
    type: Literal["email_rules"] = Field(
        default="email_rules",
        description="Type identifier for ruleset"
    )
    version: str = Field(
        ...,
        pattern="^v\\d+$",
        description="Version identifier (e.g., v2)",
        examples=["v2"]
    )
    rules: List[Rule] = Field(
        ...,
        description="List of processing rules"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "email_rules",
                    "version": "v1",
                    "rules": [
                        {
                            "id": "rule-1",
                            "name": "Auto-file newsletters",
                            "priority": 1,
                            "enabled": True,
                            "conditions": [
                                {
                                    "field": "classification.type",
                                    "operator": "eq",
                                    "value": "newsletter"
                                }
                            ],
                            "actions": [
                                {
                                    "type": "save_to_folder",
                                    "parameters": {"folder": "Newsletters"}
                                },
                                {"type": "mark_read"}
                            ]
                        }
                    ]
                }
            ]
        }
    )


class Classification(BaseModel):
    """5-tuple email classification."""
    
    reviewed: str = Field(..., examples=["no"])
    type: str = Field(..., examples=["work"])
    senderIdentity: str = Field(..., examples=["known"])
    context: str = Field(..., examples=["project"])
    handler: str = Field(..., examples=["respond"])
    confidence: Optional[Dict[str, float]] = Field(
        None,
        examples=[{
            "type": 0.95,
            "senderIdentity": 0.88,
            "context": 0.76,
            "handler": 0.92
        }]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "reviewed": "no",
                    "type": "work",
                    "senderIdentity": "known",
                    "context": "project",
                    "handler": "respond"
                }
            ]
        }
    )


class Attachment(BaseModel):
    """Email attachment information."""
    
    filename: str = Field(..., examples=["report.pdf"])
    mimeType: str = Field(..., examples=["application/pdf"])
    size: int = Field(..., ge=0, examples=[2048576])
    storagePath: Optional[str] = Field(
        None,
        description="Local path where attachment is stored",
        examples=["/data/attachments/2025-08-27/msg-123/report.pdf"]
    )
    sha256Hash: Optional[str] = Field(
        None,
        description="SHA256 hash of the attachment",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    )


class EmailFeatures(BaseModel):
    """Email features for classification."""
    
    subject: str = Field(..., examples=["Project Update - Q4 Goals"])
    body: str = Field(..., examples=["Hi team, here's the update on our Q4 goals..."])
    from_: Optional[str] = Field(None, alias="from", examples=["john.doe@company.com"])
    to: Optional[List[str]] = Field(None, examples=[["team@company.com"]])
    cc: Optional[List[str]] = Field(None, examples=[["manager@company.com"]])
    attachments: Optional[List[Attachment]] = Field(
        None,
        examples=[[
            {
                "filename": "report.pdf",
                "mimeType": "application/pdf",
                "size": 2048576,
                "storagePath": "/data/attachments/2025-08-27/msg-123/report.pdf"
            }
        ]]
    )


class EmailInfo(BaseModel):
    """Detailed email information."""
    
    subject: str
    from_: str = Field(..., alias="from")
    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    replyTo: Optional[str] = None
    receivedAt: datetime
    sentAt: Optional[datetime] = None
    bodyPreview: Optional[str] = Field(None, max_length=500)
    hasAttachments: bool = False
    attachments: Optional[List[Attachment]] = None
    attachmentCount: int = Field(0, ge=0)
    importance: Optional[str] = Field(None, pattern="^(low|normal|high)$")
    isRead: bool = False
    isFlagged: bool = False

    class Config:
        populate_by_name = True


class Decision(BaseModel):
    """Email processing decision with review tracking."""
    
    id: Optional[str] = None
    messageId: str
    timestamp: datetime
    email: EmailInfo
    classification: Classification
    rulesMatched: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    calendarConflicts: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    modelVersion: Optional[str] = None
    processingTime: Optional[float] = None
    digestIncluded: Optional[bool] = None
    # Review tracking fields
    reviewCount: int = Field(
        0,
        ge=0,
        description="Number of times this email has appeared in summaries"
    )
    reviewCountThreshold: Optional[int] = Field(
        None,
        ge=1,
        description="User-defined threshold for review count"
    )
    reviewCountExceeded: bool = Field(
        False,
        description="Flag indicating review count has exceeded threshold"
    )
    lastReviewedAt: Optional[datetime] = Field(
        None,
        description="Timestamp of last review"
    )


class FeedbackItem(BaseModel):
    """Feedback item."""
    
    decisionId: Optional[str] = None
    correctedClassification: Optional[Classification] = None
    feedback: Optional[str] = None


class FeedbackBatch(BaseModel):
    """Batch of feedback items."""
    
    items: List[FeedbackItem]


class VersionInfo(BaseModel):
    """Version information."""
    
    version: str
    createdAt: datetime
    description: Optional[str] = None


class SchedulePreview(BaseModel):
    """Schedule preview response."""
    
    schedule: str
    nextRuns: List[datetime]


class ClassificationRequest(BaseModel):
    """Email classification request."""
    
    messageId: Optional[str] = None
    subject: str
    body: str
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class ClassificationResponse(BaseModel):
    """Email classification response."""
    
    messageId: str
    timestamp: datetime
    classification: Classification
    features: EmailFeatures
    rulesMatched: List[str] = []
    actions: List[Action] = []


class GraphIngestRequest(BaseModel):
    """Graph data ingestion request."""
    
    batch: Dict[str, Any]


class GraphIngestResponse(BaseModel):
    """Graph data ingestion response."""
    
    tripleCount: int
    errors: List[str] = []


class GraphQueryResponse(BaseModel):
    """Graph query response."""
    
    columns: List[str]
    rows: List[List[Any]]


class FeedbackResponse(BaseModel):
    """Feedback processing response."""
    
    accepted: int
    graphUpserts: int
