from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.rag import retrieve
from app.schema import CorepResponse, FieldEntry
from app.validation import validate_fields, validate_total
from app.renderer import render_table
from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key="your api key here") # or you can use .env file to keep the api key safe using api_key=os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-2.5-flash" # i used a gemini-2.5-flash model here since it's a stable and fairly capable model

app = FastAPI(title="LLM-assisted COREP Reporting Assistant")


class UserInput(BaseModel):
    question: str
    scenario: str

def calculate_total_own_funds(fields):
    total = 0
    for f in fields:
        if f.row in ["010", "020", "030", "040"]:
            total += f.value
    return total


@app.post("/generate")
def generate_corep(input: UserInput):

    # we're gonna retrieve relevant regulatory text
    retrieved_chunks = retrieve(input.question + " " + input.scenario)

    # we'll now build a prompt to query the llm
    prompt = f"""
You are a regulatory reporting assistant.

Using ONLY the retrieved regulatory text below,
generate structured JSON aligned with this schema:

{{
  "template": "C01.00",
  "fields": [
    {{
      "row": "string",
      "label": "string",
      "value": number,
      "justification_refs": ["string"]
    }}
  ]
}}

Allowed rows:
010 - CET1
020 - AT1
030 - CET1 Deductions (DTAs etc.)
040 - Tier 2
050 - Total Own Funds (system calculated, DO NOT generate)

Rules:
- If deferred tax assets depend on future profitability, deduct them from CET1 (row 030).
- Deductions must be negative values.
- All values must be full numeric GBP amounts (no scaling).
- If amounts are expressed in millions (e.g., £5m), convert to full GBP values (e.g., 5000000).
- Do NOT invent new rows.
- Do NOT generate row 050.
- Return ONLY valid JSON.

Retrieved text:
{retrieved_chunks}

User question:
{input.question}

Scenario:
{input.scenario}
"""

    # here, we'll build the llm and query it
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"temperature": 0}
    )

    raw_output = response.text.strip()

    # json extraction is done in the follwoing way
    if "```" in raw_output:
        raw_output = raw_output.replace("```json", "").replace("```", "").strip()

    try:
        output_json = json.loads(raw_output)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM did not return valid JSON."
        )
    
    parsed = CorepResponse(**output_json)

    validation_errors = validate_fields(parsed.fields)

    total_value = calculate_total_own_funds(parsed.fields)

    total_field = FieldEntry(
        row="050",
        label="Total Own Funds",
        value=total_value,
        justification_refs=["System calculated"]
    )

    parsed.fields.append(total_field)

    validation_errors.extend(validate_total(parsed.fields))

    rendered_table = render_table(parsed.fields)

    # this is where we build the audit log
    audit_log = [
        {
            "row": f.row,
            "justification": f.justification_refs
        }
        for f in parsed.fields
    ]

    return {
        "retrieved_text": retrieved_chunks,
        "structured_output": parsed,
        "validation_errors": validation_errors,
        "template_extract": rendered_table,
        "audit_log": audit_log
    }