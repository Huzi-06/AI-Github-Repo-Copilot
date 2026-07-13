from pydantic import BaseModel


class IngestRequest(BaseModel):
    repo_url: str


class QARequest(BaseModel):
    repo_url: str
    question: str


class GenerateRequest(BaseModel):
    repo_url: str
    target_file: str | None = None
