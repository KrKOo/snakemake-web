from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class Executor(BaseModel):
    command: List[str]
    env: Dict[str, str]
    ignore_error: bool
    image: str
    stderr: Optional[str] = None
    stdin: str
    stdout: Optional[str] = None
    workdir: str


class InputFile(BaseModel):
    content: Optional[str] = None
    description: str
    name: str
    path: str
    streamable: bool
    type: str
    url: Optional[str]


class LogEntry(BaseModel):
    end_time: str
    exit_code: int
    start_time: Optional[datetime] = None
    stderr: str
    stdout: str


class Metadata(BaseModel):
    hostname: Optional[str] = None


class LogBlock(BaseModel):
    end_time: str
    logs: List[LogEntry]
    metadata: Metadata
    outputs: List[str]
    start_time: datetime
    system_logs: Optional[List[str]] = None


class JobModel(BaseModel):
    creation_time: datetime
    description: str
    executors: List[Executor]
    id: str
    inputs: List[InputFile]
    logs: List[LogBlock]
    name: str
    state: str