from pydantic import BaseModel
from typing import List

class FieldEntry(BaseModel):
    row: str
    label: str
    value: float
    justification_refs: List[str]

class CorepResponse(BaseModel):
    template: str
    fields: List[FieldEntry]