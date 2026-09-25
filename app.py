import streamlit as st
import re
from pypdf import PdfReader
from agent import analyze_document, detect_framework

st.set_page_config(
    page_title="AI Compliance Agent",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI Compliance Policy Checker")
st.write(
    "Analyze contracts, policy documents, and source code "
    "against compliance frameworks using an AI-powered policy engine."
)

uploaded_files = st.file_uploader(
    "Upload contracts, policy documents, or source code",
    type=["pdf", "txt", "py", "js", "java"],
    accept_multiple_files=True
)

framework = st.selectbox(
    "Select Compliance Framework",
    ["GDPR", "HIPAA", "ISO 27001", "CCPA"]
)


def extract_file_text(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    return uploaded_file.read().decode(
        "utf-8",
        errors="ignore"
    )


def detect_pii(text):
    results = []

    emails = re.findall(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text
    )

    phones = re.findall(
        r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
        text
    )

    urls = re.findall(
        r"https?://[^\s]+",
        text
    )

    if emails:
        results.append({
            "type": "Email Address",
            "count": len(set(emails)),
            "severity": "Medium",
            "examples": list(dict.fromkeys(emails))[:3]
        })

    if phones:
        results.append({
            "type": "Phone Number",
            "count": len(set(phones)),
            "severity": "High",
            "examples": list(dict.fromkeys(phones))[:3]
        })

    if urls:
        results.append({
            "type": "Web Address",
            "count": len(set(urls)),
            "severity": "Low",
            "examples": list(dict.fromkeys(urls))[:3]
        })

    return results


if uploaded_files and st.button(
    "🔍 Analyze Documents",
    use_container_width=True
):

    combined_text = ""

    for uploaded_file in uploaded_files:
        file_text = extract_file_text(uploaded_file)

        if file_text.strip():
            combined_text += (
                f"\n\n===== FILE: {uploaded_file.name} =====\n\n"
            )
            combined_text += file_text

    if not combined_text.strip():
        st.error(
            "Could not extract text from the uploaded files."
        )
        st.stop()

    progress = st.progress(0)
    status_box = st.empty()

    try:

        progress.progress(10)
        status_box.info(
            "📄 Reading uploaded documents and source files"
        )

        progress.progress(25)
        status_box.info(
            "🤖 Detecting document framework"
        )

        detection = detect_framework(combined_text)

        detected_framework = detection["framework"]
        confidence = detection["confidence"]

        if detected_framework == "Unknown":

            st.info(
                "ℹ️ The system could not confidently identify "
                "the framework from the uploaded document. "
                "The selected framework will be used."
            )

        elif detected_framework != framework:

            st.warning(
                f"⚠️ Framework mismatch detected!\n\n"
                f"**Detected framework:** {detected_framework}\n\n"
                f"**Selected framework:** {framework}\n\n"
                f"The document will be analyzed against "
                f"**{framework}** because that is the framework "
                f"you selected."
            )

        else:

            st.success(
                f"✅ Framework detected: **{detected_framework}** "
                f"with **{confidence} confidence**."
            )

        progress.progress(40)
        status_box.info(
            f"🔍 Checking {framework} requirements"
        )

        progress.progress(55)
        status_box.info(
            "🤖 Analyzing compliance requirements"
        )

        result = analyze_document(
            combined_text,
            framework
        )

        progress.progress(75)
        status_box.info(
            "⚠️ Assessing compliance risks"
        )

        pii_results = detect_pii(combined_text)

        progress.progress(90)
        status_box.info(
            "✍️ Generating remediation guidance"
        )

        progress.progress(100)

        status_box.success(
            "✅ Analysis completed successfully!"
        )

        findings = result.get(
            "findings",
            []
        )

        total = len(findings)

        compliant_count = sum(
            1
            for finding in findings
            if finding.get("status") == "Compliant"
        )

        partial_count = sum(
            1
            for finding in findings
            if finding.get("status") == "Partial"
        )

        high = sum(
            1
            for finding in findings
            if finding.get("severity") == "High"
        )

        medium = sum(
            1
            for finding in findings
            if finding.get("severity") == "Medium"
        )

        score = (
            round(
                (compliant_count / total) * 100
            )
            if total
            else 0
        )

        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Compliance Score",
            f"{score}%"
        )

        col2.metric(
            "High Risk",
            high
        )

        col3.metric(
            "Medium Risk",
            medium
        )

        col4.metric(
            "Compliant",
            compliant_count
        )

        st.subheader("📁 Files Analyzed")

        for uploaded_file in uploaded_files:

            extension = (
                uploaded_file.name
                .split(".")[-1]
                .upper()
            )

            if extension == "PY":
                icon = "🐍"
            elif extension == "JS":
                icon = "⚡"
            elif extension == "JAVA":
                icon = "☕"
            elif extension == "PDF":
                icon = "📄"
            else:
                icon = "📝"

            st.write(
                f"{icon} **{uploaded_file.name}**"
            )

        st.subheader("🔐 PII Exposure Scan")

        if pii_results:

            st.warning(
                "Potential personally identifiable "
                "information was detected."
            )

            pii_cols = st.columns(
                len(pii_results)
            )

            for i, item in enumerate(
                pii_results
            ):

                with pii_cols[i]:

                    st.metric(
                        item["type"],
                        item["count"]
                    )

                    st.write(
                        f"Severity: **{item['severity']}**"
                    )

            with st.expander(
                "View detected PII"
            ):

                for item in pii_results:

                    st.write(
                        f"**{item['type']}**"
                    )

                    st.write(
                        f"Count: {item['count']}"
                    )

                    st.write(
                        f"Severity: {item['severity']}"
                    )

                    st.write(
                        "Examples: "
                        + ", ".join(
                            item["examples"]
                        )
                    )

        else:

            st.success(
                "No obvious PII patterns detected."
            )

        st.subheader(
            "📋 Analysis Summary"
        )

        st.write(
            result.get(
                "summary",
                ""
            )
        )

        st.subheader(
            "🔎 Compliance Findings"
        )

        for finding in findings:

            severity = finding.get(
                "severity",
                ""
            )

            if severity == "High":
                icon = "🔴"
            elif severity == "Medium":
                icon = "🟠"
            else:
                icon = "🟢"

            with st.expander(
                f"{icon} "
                f"{finding.get('rule_id')} — "
                f"{finding.get('title')}"
            ):

                st.write(
                    f"**Status:** "
                    f"{finding.get('status')}"
                )

                st.write(
                    f"**Severity:** "
                    f"{severity}"
                )

                st.write(
                    f"**Evidence:** "
                    f"{finding.get('evidence')}"
                )

                st.write(
                    f"**Issue:** "
                    f"{finding.get('issue')}"
                )

                st.write(
                    f"**Recommendation:** "
                    f"{finding.get('recommendation')}"
                )

                alternative = finding.get(
                    "compliant_alternative",
                    ""
                )

                if alternative:

                    st.markdown(
                        "### ✍️ Suggested "
                        "Compliant Alternative"
                    )

                    st.info(
                        alternative
                    )

        file_names = ", ".join(
            file.name
            for file in uploaded_files
        )

        report = f"""AI COMPLIANCE REPORT

Framework: {framework}
Detected Framework: {detected_framework}
Detection Confidence: {confidence}
Files: {file_names}

Compliance Score: {score}%
High Risk Findings: {high}
Medium Risk Findings: {medium}
Partial Findings: {partial_count}
Compliant Requirements: {compliant_count}

PII EXPOSURE SCAN
"""

        if pii_results:

            for item in pii_results:

                report += f"""
{item['type']}
Count: {item['count']}
Severity: {item['severity']}
Examples: {', '.join(item['examples'])}
"""

        else:

            report += (
                "\nNo obvious PII patterns detected.\n"
            )

        report += f"""

SUMMARY
{result.get("summary", "")}

FINDINGS
"""

        for finding in findings:

            report += f"""

{finding.get('rule_id')} - {finding.get('title')}
Status: {finding.get('status')}
Severity: {finding.get('severity')}
Evidence: {finding.get('evidence')}
Issue: {finding.get('issue')}
Recommendation: {finding.get('recommendation')}
Suggested Compliant Alternative: {finding.get('compliant_alternative')}
"""

        st.divider()

        st.subheader(
            "📥 Compliance Report"
        )

        st.download_button(
            "Download Compliance Report",
            report,
            file_name=(
                f"{framework.replace(' ', '_')}"
                "_compliance_report.txt"
            ),
            mime="text/plain",
            use_container_width=True
        )

    except Exception as e:

        progress.empty()
        status_box.empty()

        st.error(
            f"Analysis failed: {e}"
        )