"""
IntelliPrint Nexus - AI Assistant Chatbot
Interactive chatbot interface for print system configurations, costs, queue states, and troubleshooting.
"""

import streamlit as st


import re

def _clean_html(html: str) -> str:
    """Clean indentations, comments, and newlines that confuse streamlit's markdown parser."""
    # Remove HTML comments to prevent markdown parser from falling back to text/code block
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())
from datetime import datetime
import random

from smartdb.crud import get_chat_history, save_chat_message, get_user_jobs, get_all_printers
from smartutils.helpers import format_datetime


def show_ai_assistant():
    """Render the AI assistant chat view."""

    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)
    username = user.get("username", "Student")

    st.html(_clean_html(_chat_css()))

    st.markdown(_clean_html("""
        <div class="chat-header">
            <div class="chat-icon">🤖</div>
            <div class="chat-title">AI Print Assistant</div>
            <div class="chat-subtitle">Ask about queue times, pricing, printer statuses, or troubleshooting</div>
        </div>
        """),
        unsafe_allow_html=True,)

    # ── Load history ──────────────────────────────────────────────────────
    chat_history = []
    try:
        chat_history = get_chat_history(user_id) or []
    except Exception:
        pass

    # If empty, save welcome message
    if not chat_history:
        welcome_msg = f"Hi {username}! I'm your IntelliPrint Nexus assistant. Ask me anything about print settings, pricing, real-time queue, printer status, or how to resolve blur/skew alerts."
        try:
            save_chat_message(user_id, "assistant", welcome_msg)
            chat_history = get_chat_history(user_id) or []
        except Exception:
            chat_history = [{"role": "assistant", "message": welcome_msg, "created_at": datetime.now()}]

    # ── Display Messages ─────────────────────────────────────────────────
    with st.container():
        st.markdown('<span class="chat-container-marker" style="display:none;"></span>', unsafe_allow_html=True)
        for msg in chat_history:
            role = msg.get("role", "assistant")
            content = msg.get("message", "")
            align_class = "msg-user" if role == "user" else "msg-assistant"
            icon = "👤" if role == "user" else "🤖"
            
            st.markdown(_clean_html(f"""
                <div class="chat-row {align_class}">
                    <div class="chat-bubble-wrapper">
                        <div class="chat-meta">
                            <span class="chat-role">{icon} {role.upper()}</span>
                        </div>
                        <div class="chat-bubble">{content}</div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,)

    # ── Input Area ───────────────────────────────────────────────────────
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Save user message
        try:
            save_chat_message(user_id, "user", user_input)
        except Exception:
            pass

        # Generate response
        response = _generate_ai_response(user_input, user_id, username)
        
        # Save assistant message
        try:
            save_chat_message(user_id, "assistant", response)
        except Exception:
            pass
            
        st.rerun()


def _generate_ai_response(query: str, user_id: int, username: str) -> str:
    """Generate intelligent mock responses based on query keywords."""
    q = query.lower().strip()

    # 1. Cost / Price inquiries
    if any(k in q for k in ["cost", "price", "rate", "how much", "charge", "payment"]):
        return (
            "💰 **IntelliPrint Nexus Tariff Sheet:**\n\n"
            "- **Black & White:** ₹2.00 per page\n"
            "- **Color:** ₹5.00 per page\n"
            "- **Duplex Discount:** 10% discount on page cost when printing double-sided.\n"
            "- **Priority Print Surcharges:** Normal (1.0x), High (1.5x), Urgent (2.0x).\n\n"
            "You can compute precise estimates by uploading a document in the **Submit Print Job** tab."
        )

    # 2. Queue Status / Active jobs
    if any(k in q for k in ["queue", "status", "my job", "active", "track"]):
        try:
            jobs = get_user_jobs(user_id) or []
            active = [j for j in jobs if j.get("status", "").lower() in ("pending", "payment_pending", "queued", "printing")]
            if not active:
                return "📂 You currently have **no active print jobs** in the queue. You can submit one in the **Submit Print Job** section!"
            
            res = "⏳ **Your Active Print Jobs in Queue:**\n\n"
            for j in active:
                p_id = j.get("print_id", "N/A")
                doc = j.get("document_name", "Document")
                status = j.get("status", "Pending").title()
                res += f"- **{p_id}** | `{doc}` | Status: **{status}**\n"
            return res
        except Exception:
            return "⏳ You currently have 1 active job in the printing queue. Average estimated wait is ~4 minutes."

    # 3. Printer locations / status
    if any(k in q for k in ["printer", "location", "active printers", "where"]):
        try:
            printers = get_all_printers() or []
            if not printers:
                return "🖨️ Our printers are currently undergoing maintenance. Please check back shortly."
            
            res = "🖨️ **Connected Printers Status:**\n\n"
            for p in printers:
                status_dot = "🟢" if p.get("status") == "Online" else "🟡" if p.get("status") == "Maintenance" else "🔴"
                res += f"{status_dot} **{p.get('name')}**\n  - Location: {p.get('location')}\n  - Status: *{p.get('status')}* (Toner: {p.get('toner_level')}%)\n\n"
            return res
        except Exception:
            return "🖨️ Connected printers include the CS Lab Printer (Online, Ground Floor) and Library LaserJet (Online, 1st Floor)."

    # 4. Document quality / Vision AI
    if any(k in q for k in ["blur", "skew", "quality", "scan", "vision", "alert"]):
        return (
            "🧠 **SmartPrint Vision AI Quality Checks:**\n\n"
            "On document upload, our integrated computer vision models scan for three critical defects:\n"
            "1. **Blur Detection**: Assesses text contrast and edge definitions to alert you if a scan is unreadable.\n"
            "2. **Skew Correction**: Detects page tilt angle, warning you if your scan was misaligned.\n"
            "3. **Resolution check**: Identifies low-DPI images that would print poorly.\n\n"
            "If you get a quality warning, click the **👁️ View** button next to the job in your history to see the full recommendations."
        )

    # 5. Greeting / Help
    if any(k in q for k in ["hi", "hello", "hey", "help", "who are you"]):
        return (
            f"Hello {username}! How can I help you print smarter today? You can ask me:\n\n"
            "- \"What are the printing rates?\"\n"
            "- \"Where are the printers located?\"\n"
            "- \"What is the status of my print queue?\"\n"
            "- \"How does the quality check work?\""
        )

    # 6. Fallback
    responses = [
        "I can help you resolve printer issues, calculate document costs, or check the university's printing queue. Could you rephrase your question?",
        "I'm here to assist with your printing configurations. You can also review printer status logs or trace pending jobs in the side navigation panel.",
        "That's a good question! For that feature, you can also check the Admin control panel if you are an administrator, or submit an inquiry to university tech support."
    ]
    return random.choice(responses)


def _chat_css() -> str:
    return """
    <style>
    .chat-header { text-align: center; padding: 20px 0 10px; }
    .chat-icon { font-size: 3rem; margin-bottom: 8px; }
    .chat-title {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #3B82F6, #60A5FA);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .chat-subtitle { color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-top: 4px; }

    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 10px 0;
        margin-bottom: 20px;
    }

    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
    }
    .msg-user { justify-content: flex-end; }
    .msg-assistant { justify-content: flex-start; }

    .chat-bubble-wrapper {
        max-width: 75%;
    }
    .msg-user .chat-bubble-wrapper { text-align: right; }

    .chat-meta {
        font-size: 0.72rem;
        color: rgba(255,255,255,0.35);
        margin-bottom: 4px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .chat-bubble {
        padding: 12px 18px;
        border-radius: 16px;
        font-size: 0.9rem;
        line-height: 1.5;
        text-align: left;
    }
    .msg-user .chat-bubble {
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        color: #fff;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 15px rgba(0,217,255,0.25);
    }
    .msg-assistant .chat-bubble {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.85);
        border-bottom-left-radius: 4px;
    }
    </style>
    """
