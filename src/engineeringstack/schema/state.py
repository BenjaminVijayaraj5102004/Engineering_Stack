"""State and message schemas for the EngineeringStack multi-agent pipeline."""

import re
from typing import Any, Optional, Union
from langchain_core.messages import AIMessage, HumanMessage
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

    def to_prompt(self) -> str:
        """Format the UserInput schema fields into a structured user prompt."""
        parts = [f"User Request: {self.query}"]
        if self.requirements:
            parts.append(f"Requirements: {self.requirements}")
        if self.framework:
            parts.append(f"Framework: {self.framework}")
        if self.language:
            parts.append(f"Language: {self.language}")
        if self.database:
            parts.append(f"Database: {self.database}")
        return "\n".join(parts)

    def to_payload(self) -> dict[str, Any]:
        """Convert UserInput schema into a standard LangGraph state payload."""
        return {"messages": [{"role": "user", "content": self.to_prompt()}]}

    @classmethod
    def from_input(cls, input_data: Any) -> "UserInput":
        """Construct UserInput from string, dict, or existing UserInput instance."""
        if isinstance(input_data, cls):
            return input_data
        if isinstance(input_data, str):
            return cls(query=input_data)
        if isinstance(input_data, dict):
            if "query" in input_data:
                return cls(**input_data)
            if "messages" in input_data and input_data["messages"]:
                last_user_content = ""
                for msg in input_data["messages"]:
                    if isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", str(msg))
                    else:
                        role = "user" if isinstance(msg, HumanMessage) else "assistant"
                        content = getattr(msg, "content", str(msg))
                    if role == "user":
                        last_user_content = str(content)
                return cls(query=last_user_content or "User request")
            return cls(query=str(input_data))
        return cls(query=str(input_data))


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
        description="Summary bullet points or text describing the solution.",
    )
    code: str = Field(
        description="The generated source code or implementation output.",
    )

    @classmethod
    def from_messages(cls, messages: list) -> "AIOutput":
        """Automatically parse LangGraph messages into structured AIOutput format."""
        final_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                if msg.content and not getattr(msg, "tool_calls", None):
                    final_text = str(msg.content)
                    break
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                if msg.get("content"):
                    final_text = str(msg["content"])
                    break

        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", final_text, re.DOTALL)
        if code_blocks:
            code_content = "\n\n".join(cb.strip() for cb in code_blocks)
        else:
            code_content = final_text.strip()

        bullets: list[str] = []
        for line in final_text.splitlines():
            line_str = line.strip()
            if line_str.startswith(("-", "*", "•")) or (
                re.match(r"^\d+\.", line_str) and len(line_str) > 3
            ):
                cleaned = re.sub(r"^[\-\*\•\d\.]+\s*", "", line_str).strip()
                if cleaned and cleaned not in bullets:
                    bullets.append(cleaned)

        if not bullets and final_text:
            non_code_text = re.sub(r"```(?:\w+)?\n.*?```", "", final_text, flags=re.DOTALL).strip()
            for line in non_code_text.splitlines():
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#") and clean_line not in bullets:
                    bullets.append(clean_line)

        return cls(summary=bullets, code=code_content)
