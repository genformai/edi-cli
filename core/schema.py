from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Delimiters(BaseModel):
    segment: str = Field(..., alias="segment")
    element: str = Field(..., alias="element")
    sub_element: str = Field(..., alias="sub_element")

class Element(BaseModel):
    name: str
    type: str

class Segment(BaseModel):
    name: str
    elements: List[Element]

class Schema(BaseModel):
    delimiters: Delimiters
    segments: dict[str, Segment]

class EdiSchema(BaseModel):
    schema_definition: Schema = Field(..., alias="schema")
