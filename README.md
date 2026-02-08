# LLM-Assisted PRA COREP Reporting Assistant (Prototype)

## Overview

This project is a prototype of an **LLM-assisted regulatory reporting assistant** for PRA COREP returns.

COREP reporting requires interpreting dense regulatory rules (CRR, PRA Rulebook) and mapping them into structured reporting templates. This process is manual, time-consuming, and error-prone.

This prototype demonstrates an end-to-end workflow:

> **User question → Regulatory retrieval → Structured LLM output → Validation → Populated COREP template extract**

The system focuses on a constrained subset of **COREP Template C01.00 (Own Funds)** to demonstrate correctness, auditability, and deterministic validation.

---

## Scope

Supported template: **C01.00 – Own Funds**

Supported rows:

| Row | Description |
|------|-------------|
| 010 | Common Equity Tier 1 (CET1) |
| 020 | Additional Tier 1 (AT1) |
| 030 | CET1 Deductions (e.g., Deferred Tax Assets) |
| 040 | Tier 2 Capital |
| 050 | Total Own Funds (System-calculated) |

The LLM is responsible for regulatory interpretation.  
The system is responsible for validation and total calculation.

---

## Architecture

### 1. Retrieval (RAG)
- Regulatory text chunks (CRR, PRA Own Funds, COREP instructions)
- Embedded using `gemini-embedding-001`
- Similarity search retrieves relevant paragraphs

### 2. Structured LLM Generation
- Model: `gemini-2.5-flash`
- Temperature set to 0 (deterministic behaviour)
- Constrained JSON output aligned to a predefined schema
- LLM does **not** calculate totals

### 3. Validation Layer
- Ensures only allowed rows are generated
- Ensures deductions are negative
- Calculates Total Own Funds internally
- Flags missing or inconsistent data

### 4. Rendering & Audit
- Produces human-readable COREP template extract
- Returns validation errors
- Provides audit log linking populated rows to regulatory references

---

## Example Scenario

**Input**

> The bank has £10m CET1 capital and £5m deferred tax assets dependent on future profitability.

**Output**

| Row | Label | Amount |
|------|--------|--------|
| 010 | CET1 | 10,000,000 |
| 030 | CET1 Deductions | -5,000,000 |
| 050 | Total Own Funds | 5,000,000 |

The audit log references CRR Article 36 and PRA Own Funds guidance used to justify the deduction.

---

## Design Principles

- **Deterministic Controls:** Totals and validation are handled by the system, not the LLM.
- **Constrained Scope:** Limited to a subset of one COREP template to prioritise correctness.
- **Traceability:** Each populated field includes regulatory justification references.
- **Risk Awareness:** The LLM assists interpretation but is not treated as authoritative.

---

## Assumptions & Limitations

- Simplified regulatory corpus (static sample text)
- GBP currency only
- No live PRA taxonomy integration
- No XBRL export functionality
- Limited to selected rows within C01.00

This is a feasibility prototype, not a production-ready regulatory reporting system.

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get your own api key from [Google AI Studio](https://aistudio.google.com/app/api-keys)

### 3. Now, run the prototype in the main directory(corep-assisstant/) using:


```bash
uvicorn app.main:app
```

### 4. Test Cases:

To test the api- we head over to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), after running the prototype.

The input:
```bash
{
  "question": "How should deferred tax assets be treated?",
  "scenario": "The bank has £10m CET1 capital and £5m deferred tax assets dependent on future profitability."
}
```
The output:

```bash
{
  "retrieved_text": [
    "CRR Article 36(1)(c):\nDeferred tax assets that rely on future profitability shall be deducted from CET1 capital.",
    "PRA Own Funds 2.2:\nFirms must apply deductions for DTAs dependent on future taxable profit.",
    "COREP C01.00 Instructions:\nRow 030 corresponds to deductions from CET1 including deferred tax assets.\nRow 010 corresponds to Common Equity Tier 1 capital.\nRow 020 corresponds to Additional Tier 1 capital.\nRow 040 corresponds to Tier 2 capital."
  ],
  "structured_output": {
    "template": "C01.00",
    "fields": [
      {
        "row": "010",
        "label": "CET1",
        "value": 10000000,
        "justification_refs": [
          "COREP C01.00 Instructions"
        ]
      },
      {
        "row": "030",
        "label": "CET1 Deductions (DTAs etc.)",
        "value": -5000000,
        "justification_refs": [
          "CRR Article 36(1)(c)",
          "PRA Own Funds 2.2",
          "COREP C01.00 Instructions"
        ]
      },
      {
        "row": "050",
        "label": "Total Own Funds",
        "value": 5000000,
        "justification_refs": [
          "System calculated"
        ]
      }
    ]
  },
  "validation_errors": [],
  "template_extract": [
    {
      "Row": "010",
      "Label": "CET1",
      "Amount": 10000000
    },
    {
      "Row": "030",
      "Label": "CET1 Deductions (DTAs etc.)",
      "Amount": -5000000
    },
    {
      "Row": "050",
      "Label": "Total Own Funds",
      "Amount": 5000000
    }
  ],
  "audit_log": [
    {
      "row": "010",
      "justification": [
        "COREP C01.00 Instructions"
      ]
    },
    {
      "row": "030",
      "justification": [
        "CRR Article 36(1)(c)",
        "PRA Own Funds 2.2",
        "COREP C01.00 Instructions"
      ]
    },
    {
      "row": "050",
      "justification": [
        "System calculated"
      ]
    }
  ]
}
```