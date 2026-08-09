"""State and message schemas for the EngineeringStack multi-agent pipeline."""

from typing import Optional
from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """Represents the original request received from the SDK user before any reasoning."""

    query: str = Field(
        ...,
        description="The primary request or question provided by the SDK user.",
    )
    requirements: Optional[str] = Field(
        default=None,
        description="Extracted functional or technical requirements for the task.",
    )
    framework: Optional[str] = Field(
        default=None,
        description="Target framework requested (e.g., Flask, FastAPI, Express, Django).",
    )
    language: Optional[str] = Field(
        default=None,
        description="Target programming language requested (e.g., Python, TypeScript, Go).",
    )
    database: Optional[str] = Field(
        default=None,
        description="Target database system requested (e.g., PostgreSQL, MongoDB, Redis).",
    )


class MainAgentOutput(BaseModel):
    """Represents the structured decision produced by the Main Agent before delegating work."""

    requirements: Optional[str] = Field(
        default=None,
        description="Summary of extracted requirements for routing and context.",
    )
    framework: Optional[str] = Field(
        default=None,
        description="Identified target framework for the implementation.",
    )
    manager: Optional[str] = Field(
        default=None,
        description="Manager routing decision: API_Manager, Database_Manager, or Code_Reviewer.",
    )
    specialist: Optional[str] = Field(
        default=None,
        description=(
            "Specialist agent decision: REST_Agent, GraphQL_Agent, GRPC_Agent, SOAP_Agent, "
            "RDMS_Agent, NoSQL_Agent, Redis_Agent, or Code_Reviewer."
        ),
    )


class AIOutput(BaseModel):
    """Represents the final response returned to the SDK user."""

    summary: list[str] | str | None = Field(
        default=None,
        description="Exactly five concise summary bullet points describing the solution.",
    )
    code: str = Field(
        description="The generated source code or implementation output.",
    )
