import re
import logging

# Set up logging (you can configure this elsewhere in your app)
logging.basicConfig(level=logging.INFO)

DOCUMENT_INSTRUCTIONS = {
    "elevator pitch": (
        "Keep it concise (2–3 sentences), emotionally engaging, and clearly state the problem and solution. "
        "Emphasize uniqueness and value proposition. Tailor it for quick delivery in high-stakes conversations. "
        "For any missing information such as company name, market size, or key achievements, use a [fill here] placeholder."
    ),
    "pitch deck": (
        "Break content into slide-friendly sections. Include problem, solution, market size, business model, "
        "traction, team, and financials. Keep language clear and persuasive. Use bullet points and short headers. "
        "If any data (e.g. team roles, investment numbers, market share) is not available, insert a [fill here] marker and create structured placeholders."
    ),
    "sales pitch": (
        "Focus on value proposition, ROI, and urgency. Use persuasive language tailored to the customer's pain points. "
        "If details like client industry, revenue impact, or success metrics are unknown, add [fill here] placeholders to be completed later."
    ),
    "brochure": (
        "Make it visually digestible with section headings. Highlight features, benefits, and credibility (testimonials or awards). "
        "If specific examples, awards, customer names, or statistics are missing, use [fill here] in their place for later completion."
    ),
    "one pager": (
        "Keep it tightly focused — problem, solution, key benefits, and a call to action. Use short paragraphs and bullet points. "
        "For any details like pricing, dates, or performance metrics that are not provided, include [fill here] as a placeholder."
    ),
    "industry brochure": (
        "Position the product/service in the context of specific industry challenges. Use industry terms where appropriate. "
        "Include use cases, performance metrics, and social proof relevant to that sector. Use [fill here] if any industry stats, clients, or names are not available."
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
