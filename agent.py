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

def call_agent(instruction):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are an AI compliance analysis agent. Return only valid JSON."
            },
            {
                "role": "user",
                "content": instruction
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    return json.loads(response.choices[0].message.content)

def analyze_document(document_text, framework):

    rules = FRAMEWORK_RULES[framework]

    rules_text = "\n".join(
        f"{rule['id']}: {rule['title']} - {rule['requirement']}"
        for rule in rules
    )

    analysis = call_agent(f"""
Analyze this organizational document for {framework} compliance.

Framework:
{framework}

Rules:
{rules_text}

Document:
{document_text}

Identify the exact document text relevant to each rule.

Return JSON:
{{
    "document_summary": "short summary",
    "relevant_sections": [
        {{
            "rule_id": "rule id",
            "evidence": "relevant text from document"
        }}
    ]
}}

Do not invent evidence.
""")

    compliance = call_agent(f"""
You are the compliance checking agent.

Evaluate the document against the {framework} requirements.

Rules:
{rules_text}

Document analysis:
{json.dumps(analysis)}

Evaluate every rule.

Return JSON:
{{
    "findings": [
        {{
            "rule_id": "rule id",
            "title": "rule title",
            "status": "Compliant",
            "evidence": "exact document evidence",
            "issue": "clear explanation of the compliance status"
        }}
    ]
}}

Status must be Compliant, Partial, or Violation.

For Compliant findings, explain why the requirement is adequately addressed.

For Partial findings, explain exactly what is missing or incomplete.

For Violation findings, explain the compliance gap.

Do not invent evidence.
""")

    risks = call_agent(f"""
You are the risk assessment agent.

Assess the compliance findings for {framework}.

Findings:
{json.dumps(compliance)}

Return JSON:
{{
    "findings": [
        {{
            "rule_id": "rule id",
            "title": "rule title",
            "status": "Compliant",
            "severity": "Low",
            "evidence": "evidence",
            "issue": "issue"
        }}
    ]
}}

Severity must be Low, Medium, or High.

Compliant findings should normally have Low severity.
Partial findings should normally have Medium severity.
Violation findings should normally have High severity.

Keep the evidence and issue accurate.
""")

    recommendations = call_agent(f"""
You are the remediation agent for a compliance policy engine.

Create remediation guidance for the following {framework} findings.

Risk assessment:
{json.dumps(risks)}

Return JSON:
{{
    "summary": "short overall summary",
    "findings": [
        {{
            "rule_id": "rule id",
            "title": "rule title",
            "status": "Compliant",
            "severity": "Low",
            "evidence": "evidence",
            "issue": "issue",
            "recommendation": "specific recommended action",
            "compliant_alternative": "replacement policy or contract wording"
        }}
    ]
}}

Every finding MUST contain compliant_alternative.

For Compliant findings, provide improved wording when useful.

For Partial or Violation findings, rewrite the problematic or incomplete requirement into clear policy or contract language that addresses the identified issue.

The alternative must be practical and suitable for insertion into the document.

Do not invent organizational facts.

Do not claim that the wording guarantees legal compliance.
""")

    for finding in recommendations.get("findings", []):
        if not finding.get("compliant_alternative"):
            status = finding.get("status")
            title = finding.get("title")
            issue = finding.get("issue")

            if status == "Partial":
                finding["compliant_alternative"] = (
                    f"The organization should update its policy to clearly address "
                    f"{title.lower()}. The policy should specifically define the "
                    f"applicable requirements and procedures and should address the "
                    f"identified gap: {issue}"
                )

            elif status == "Violation":
                finding["compliant_alternative"] = (
                    f"The organization should establish and document controls "
                    f"addressing {title.lower()}, including clear procedures, "
                    f"responsibilities, and safeguards appropriate to the identified risk."
                )

            else:
                finding["compliant_alternative"] = (
                    f"The organization should continue maintaining clear documentation "
                    f"covering {title.lower()} and review it periodically."
                )

    return recommendations