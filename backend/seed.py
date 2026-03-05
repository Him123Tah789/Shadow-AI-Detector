"""Seed the tools_catalog table with well-known AI domains."""

SEED_TOOLS = [
    # Chat / General AI
    {"domain": "chatgpt.com",       "name": "ChatGPT",        "category": "chat",  "base_risk_score": 6},
    {"domain": "chat.openai.com",   "name": "ChatGPT (old)",  "category": "chat",  "base_risk_score": 6},
    {"domain": "claude.ai",         "name": "Claude",          "category": "chat",  "base_risk_score": 6},
    {"domain": "gemini.google.com", "name": "Gemini",          "category": "chat",  "base_risk_score": 4},
    {"domain": "bard.google.com",   "name": "Bard (legacy)",   "category": "chat",  "base_risk_score": 4},
    {"domain": "poe.com",           "name": "Poe",             "category": "chat",  "base_risk_score": 7},
    {"domain": "perplexity.ai",     "name": "Perplexity",      "category": "chat",  "base_risk_score": 5},
    {"domain": "you.com",           "name": "You.com",         "category": "chat",  "base_risk_score": 5},
    {"domain": "character.ai",      "name": "Character.AI",    "category": "chat",  "base_risk_score": 7},
    {"domain": "pi.ai",             "name": "Pi",              "category": "chat",  "base_risk_score": 5},

    # Code
    {"domain": "github.com/copilot","name": "GitHub Copilot",  "category": "code",  "base_risk_score": 4},
    {"domain": "replit.com",         "name": "Replit AI",       "category": "code",  "base_risk_score": 7},
    {"domain": "codeium.com",        "name": "Codeium",        "category": "code",  "base_risk_score": 5},
    {"domain": "cursor.com",         "name": "Cursor",         "category": "code",  "base_risk_score": 5},
    {"domain": "phind.com",          "name": "Phind",          "category": "code",  "base_risk_score": 5},

    # Image generation
    {"domain": "midjourney.com",         "name": "Midjourney",      "category": "image", "base_risk_score": 6},
    {"domain": "labs.openai.com",        "name": "DALL-E",          "category": "image", "base_risk_score": 6},
    {"domain": "stability.ai",          "name": "Stable Diffusion","category": "image", "base_risk_score": 6},
    {"domain": "leonardo.ai",           "name": "Leonardo AI",     "category": "image", "base_risk_score": 6},
    {"domain": "ideogram.ai",           "name": "Ideogram",        "category": "image", "base_risk_score": 5},

    # File / document tools
    {"domain": "notebooklm.google.com", "name": "NotebookLM",     "category": "file",  "base_risk_score": 5},
    {"domain": "gamma.app",             "name": "Gamma",           "category": "file",  "base_risk_score": 7},
    {"domain": "tome.app",              "name": "Tome",            "category": "file",  "base_risk_score": 7},
    {"domain": "jasper.ai",             "name": "Jasper",          "category": "file",  "base_risk_score": 6},
    {"domain": "copy.ai",              "name": "Copy.ai",         "category": "file",  "base_risk_score": 6},
]


def seed_tools(db):
    from models import ToolCatalog
    existing = {t.domain for t in db.query(ToolCatalog).all()}
    for tool in SEED_TOOLS:
        if tool["domain"] not in existing:
            db.add(ToolCatalog(**tool))
    db.commit()
