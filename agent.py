import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from rules import FRAMEWORK_RULES

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def detect_framework(document_text):
    text = document_text.lower()

    framework_keywords = {
        "GDPR": [
            "gdpr",
            "general data protection regulation",
            "data subject",
            "data protection officer",
            "right to erasure",
            "right to access",
            "lawful basis",
            "personal data",
            "data protection"
        ],
        "HIPAA": [
            "hipaa",
            "health insurance portability",
            "protected health information",
            "phi",
            "patient information",
            "covered entity",
            "business associate",
            "health information"
        ],
        "ISO 27001": [
            "iso 27001",
            "iso/iec 27001",
            "isms",
            "information security management system",
            "information security policy",
            "risk management",
            "access control",
            "business continuity",
            "security monitoring",
            "asset management",
            "incident management"
        ],
        "CCPA": [
            "ccpa",
            "california consumer privacy act",
            "california privacy rights act",
            "consumer privacy",
            "consumer personal information",
            "right to opt out",
            "sale of personal information",
            "sharing of personal information"
        ]
    }

    scores = {}

    for framework, keywords in framework_keywords.items():
        score = 0

        for keyword in keywords:
            if keyword in text:
                if keyword in [
                    "gdpr",
                    "hipaa",
                    "iso 27001",
                    "iso/iec 27001",
                    "ccpa"
                ]:
                    score += 5
                else:
                    score += 1

        scores[framework] = score

    detected_framework = max(scores, key=scores.get)
    highest_score = scores[detected_framework]

    if highest_score == 0:
        return {
            "framework": "Unknown",
            "confidence": "Low",
            "scores": scores
        }

    sorted_scores = sorted(
        scores.values(),
        reverse=True
    )

    if highest_score >= 5:
        confidence = "High"
    elif highest_score >= 3:
        confidence = "Medium"
    else:
        confidence = "Low"

    if len(sorted_scores) > 1:
        second_score = sorted_scores[1]

        if highest_score - second_score <= 1:
            confidence = "Low"

    return {
        "framework": detected_framework,
        "confidence": confidence,
        "scores": scores
    }


def analyze_document(document_text, framework):
    rules = FRAMEWORK_RULES[framework]

    rules_text = "\n".join(
        f"{rule['id']}: {rule['title']} - {rule['requirement']}"
        for rule in rules
    )

    schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string"
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_id": {
                            "type": "string"
                        },
                        "title": {
                            "type": "string"
                        },
                        "status": {
                            "type": "string",
                            "enum": [
                                "Compliant",
                                "Partial",
                                "Violation"
                            ]
                        },
                        "severity": {
                            "type": "string",
                            "enum": [
                                "Low",
                                "Medium",
                                "High"
                            ]
                        },
                        "evidence": {
                            "type": "string"
                        },
                        "issue": {
                            "type": "string"
                        },
                        "recommendation": {
                            "type": "string"
                        },
                        "compliant_alternative": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "rule_id",
                        "title",
                        "status",
                        "severity",
                        "evidence",
                        "issue",
                        "recommendation",
                        "compliant_alternative"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": [
            "summary",
            "findings"
        ],
        "additionalProperties": False
    }

    prompt = f"""
You are an AI compliance policy checker.

Analyze the provided document against the {framework} framework.

RULES:
{rules_text}

DOCUMENT:
{document_text}

Instructions:

1. Evaluate every rule.
2. Use only information present in the document.
3. Never invent evidence.
4. Status must be exactly:
   Compliant, Partial, or Violation.
5. Severity must be exactly:
   Low, Medium, or High.
6. For Compliant findings, explain why the requirement is addressed.
7. For Partial findings, explain what is missing.
8. For Violation findings, explain the compliance gap.
9. Provide a practical recommendation.
10. Provide suitable replacement wording when needed.
11. Return one finding for every rule.
12. Return valid JSON matching the provided schema.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "compliance_report",
                    "strict": True,
                    "schema": schema
                }
            },
            reasoning_effort="low",
            max_completion_tokens=12000,
            temperature=0
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt + "\nReturn JSON only."
                    }
                ],
                response_format={
                    "type": "json_object"
                },
                reasoning_effort="low",
                max_completion_tokens=12000,
                temperature=0
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            if "summary" in result and "findings" in result:
                return result

        except Exception:
            pass

        findings = []

        for rule in rules:
            findings.append({
                "rule_id": rule["id"],
                "title": rule["title"],
                "status": "Partial",
                "severity": "Medium",
                "evidence": "No reliable AI evidence could be generated.",
                "issue": rule["requirement"],
                "recommendation": "Review the document against this requirement.",
                "compliant_alternative": rule["requirement"]
            })

        return {
            "summary": f"Compliance analysis completed for {framework}. Manual review is recommended for the identified requirements.",
            "findings": findings
        }