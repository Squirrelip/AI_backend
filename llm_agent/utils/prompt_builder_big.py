import re
import logging

# Set up logging (you can configure this elsewhere in your app)
logging.basicConfig(level=logging.INFO)

DOCUMENT_INSTRUCTIONS = {
    "competitors analysis": (
        "Provide a detailed comparison of direct and indirect competitors. Include company size, market share, "
        "product/service differentiation, pricing strategy, strengths, and weaknesses. Use tables or bullet points "
        "where appropriate. If data is missing (e.g., exact revenue or market share), include a [fill here] placeholder. "
        "If monetary results (e.g., profitability or valuation) are mentioned, refer to any relevant formulae found via internet search and return them as is."
    ),
    "swot analysis": (
        "Generate a structured SWOT analysis. Include Strengths, Weaknesses, Opportunities, and Threats. Each section "
        "should contain 3-5 bullet points, focused on internal and external strategic factors relevant to the firm or product. "
        "In case of strategic evaluation involving monetary estimates, include known formulae from trusted sources online."
    ),
    "target firms": (
        "Identify ideal acquisition or partnership targets based on market, business model, and strategic alignment. "
        "Include company name, size, key offerings, and justification for selection. If needed, insert placeholders like [fill here]. "
        "Use web search to identify any monetary valuation methods applicable and return them directly. Where patents are involved, "
        "search recursively for the closest 5 related patents and provide relevant comparative information."
    ),
    "patent valuation": (
        "Summarize the patent’s value using factors like market applicability, IP landscape, legal status, and licensing potential. "
        "Mention comparable patent sales if available. Use estimated ranges and include [fill here] for missing specifics. "
        "Additionally, perform a recursive search to find the 5 closest patents and their associated metadata for comparison. "
        "If valuation methods involve monetary calculations, include any formulae found on the internet.",
        "Do not include any value of patent in the output."

    ),
    "market place": (
        "Describe the competitive landscape, pricing models, buyer/seller personas, transaction volumes, and growth trends. "
        "Use structured subheadings (e.g., Overview, Trends, Challenges) and add [fill here] where detailed data is required. "
        "If price modeling or market sizing includes monetary formulas, source them from online references and return directly. "
        "If patent-backed innovation is part of the landscape, include a comparison of the 5 closest patents."
    )
}




FORBIDDEN_PATTERNS = [
    r"(?i)\b(ignore|disregard|forget|override|replace|stop following)\b",
    r"(?i)\b(system prompt|new instructions|act as|you are no longer)\b",
    r"(?i)\bpretend\b",
    r"(?i)\bchatgpt\b",
    r"(?i)\btask is\b.*?\bwrite\b"
]

def sanitize_instructions(text: str) -> tuple[str, bool]:
    """Sanitize additional instructions and flag if redactions were needed."""
    redacted = False
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            redacted = True
            text = re.sub(pattern, "[REDACTED]", text)
    return text.strip(), redacted

def build_prompts(document_type: str, context: str, additional_info: str = ""):
    type_key = document_type.lower()
    type_instructions = DOCUMENT_INSTRUCTIONS.get(type_key, "")
    
    safe_info, redacted = sanitize_instructions(additional_info)

    # 🚨 Log or alert if any suspicious instructions were detected
    if redacted:
        logging.warning(f"[Prompt Sanitation] Potential injection attempt in `additional_info`: {additional_info}")

    system_prompt = f"""
    You are an expert content creator. Your task is to write a professional {document_type}.
    Follow these guidelines:
    - {type_instructions}
    - The user also noted: {safe_info}
    Ensure the content is well-structured, clear, and aligned with the user's objective.
    """

    user_prompt = f"""
    Based on the following document context, create a {document_type}.

    --- DOCUMENT CONTEXT ---
    {context}
    """

    return system_prompt.strip(), user_prompt.strip()
