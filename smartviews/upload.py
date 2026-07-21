"""
SmartPrint AI - Batch Document Upload
Extended with:
  - AI Document Quality Analyzer (OpenCV / TensorFlow CNN fallback)
  - Smart Printer Selection with availability visualization
  - AI Printer Recommendation Engine (⭐)
  - Wait Time Prediction (XGBoost / Random Forest)
  - Complete student workflow: Upload → AI Analysis → Printer → Payment
"""

import streamlit as st
import re
import os
import random
from datetime import datetime, timedelta

from smartutils.helpers import calculate_cost, generate_print_id, generate_qr_code, write_log
from smartdb.crud import create_print_job, create_ai_analysis, get_all_printers, get_print_jobs_for_printer
from smartai.wait_time import predict_wait_time
from smartai.recommendation import recommend_printers
from smartai.document_quality import analyze_document_quality


def _clean_html(html: str) -> str:
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    return "".join(line.strip() for line in html.splitlines())


# ─────────────────────────────────────────────────────────────────────────────
# AI Quality Analysis helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run_quality_analysis(file_data: bytes, filename: str) -> dict:
    """
    Run AI quality analysis on uploaded PDF bytes.
    Saves a temp copy, runs analyze_document_quality, cleans up.
    Falls back to heuristic analysis if OpenCV/TF unavailable.
    """
    import tempfile, hashlib

    # Try to extract first page as image for CNN analysis
    image_path = None
    try:
        import fitz  # PyMuPDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        doc = fitz.open(tmp_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        image_path = tmp_path.replace(".pdf", ".png")
        pix.save(image_path)
        doc.close()
        os.unlink(tmp_path)
    except Exception:
        image_path = None  # Will use heuristic fallback

    result = analyze_document_quality(image_path or "")

    # Clean up temp image
    if image_path and os.path.exists(image_path):
        try:
            os.unlink(image_path)
        except Exception:
            pass

    # Enrich with file-size heuristics
    size_kb = len(file_data) / 1024
    if size_kb < 5:
        result["quality_score"] = min(result["quality_score"], 60)
        result["category"] = "Low Quality Scan"
        result["recommendation"] = "User Review Required"
    elif size_kb > 500:
        result["quality_score"] = max(result["quality_score"], 88)

    return result


def _quality_label(score: int) -> tuple:
    """Return (label, color) for a quality score."""
    if score >= 90:
        return "Excellent", "#10b981"
    elif score >= 75:
        return "Good", "#06b6d4"
    elif score >= 55:
        return "Average", "#f59e0b"
    else:
        return "Poor", "#ef4444"


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

def show_upload():
    """Render the full upload & print workflow page."""
    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)
    username = user.get("username", "Student")

    st.html(_clean_html(_upload_css()))

    # ── Header ───────────────────────────────────────────────────────────────
    with st.container():
        st.markdown(_clean_html("""
            <div class="upload-header">
                <div class="upload-icon">📤</div>
                <div class="upload-title">Smart Document Upload</div>
                <div class="upload-subtitle">AI-powered quality analysis &amp; intelligent printer selection</div>
            </div>
            """), unsafe_allow_html=True)

    # Post-submission success screen
    if st.session_state.get("upload_success"):
        _show_success_screen()
        return

    # ── SECTION 1: File Upload & Print Settings ───────────────────────────
    st.markdown(_clean_html('<div class="section-title">📂 Choose Files &amp; Settings</div>'), unsafe_allow_html=True)
    with st.container():
        col_file, col_settings = st.columns([1.2, 1])

        with col_file:
            uploaded_files = st.file_uploader(
                "Choose PDF files (Max 10)",
                type=["pdf"],
                accept_multiple_files=True,
                help="Upload multiple PDFs at once.",
                key="pdf_uploader",
                label_visibility="collapsed"
            )
            if not uploaded_files:
                st.markdown(_clean_html("""
                    <div class="upload-dropzone">
                        <div style="font-size:2.5rem;margin-bottom:8px;">📄</div>
                        <div style="font-size:0.95rem;font-weight:600;color:rgba(255,255,255,0.7);">
                            Drag and drop your PDFs here
                        </div>
                        <div style="font-size:0.8rem;color:rgba(255,255,255,0.35);margin-top:4px;">
                            AI quality analysis runs automatically after upload
                        </div>
                    </div>
                    """), unsafe_allow_html=True)

        with col_settings:
            st.markdown('<div style="font-size:0.9rem;font-weight:700;color:#fff;margin-bottom:10px;">Configure Print Parameters</div>', unsafe_allow_html=True)
            global_copies = st.number_input("Copies", min_value=1, max_value=100, value=1)
            global_color = st.selectbox("Color Mode", options=["Black & White", "Color"], index=0)
            global_duplex = st.selectbox("Print Sides", options=["Single-sided", "Double-sided"], index=0)
            priority = st.toggle("⚡ Priority Print (+50% cost)", value=False)

    if not uploaded_files:
        return

    is_color = global_color == "Color"
    is_duplex = global_duplex == "Double-sided"
    priority_str = "High" if priority else "Normal"
    color_mode_db = "Color" if is_color else "BW"

    # ── SECTION 2: AI Document Quality Analysis ───────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">🧠 AI Document Quality Analysis</div>'), unsafe_allow_html=True)

    file_details = []
    total_batch_cost = 0.0
    total_batch_pages = 0
    all_quality_ok = True

    with st.container():
        st.markdown(_clean_html("""
            <div class="ai-banner">
                <span class="ai-banner-icon">🤖</span>
                <span class="ai-banner-text">
                    Running CNN (MobileNetV2 Transfer Learning) + OpenCV analysis on your documents...
                </span>
            </div>
            """), unsafe_allow_html=True)

        for idx, f in enumerate(uploaded_files):
            file_data = f.getvalue()
            file_size_kb = len(file_data) / 1024
            estimated_pages = max(1, int(file_size_kb / 50))
            total_batch_pages += estimated_pages * global_copies

            cost_dict = calculate_cost(
                pages=estimated_pages,
                copies=global_copies,
                color_mode=color_mode_db,
                priority=priority_str,
                duplex=is_duplex,
            )
            file_cost = cost_dict["total_cost"]
            total_batch_cost += file_cost

            # Run AI quality analysis
            with st.spinner(f"Analyzing {f.name}..."):
                quality = _run_quality_analysis(file_data, f.name)

            score = quality["quality_score"]
            label, color = _quality_label(score)
            category = quality["category"]
            recommendation = quality["recommendation"]
            model_type = quality.get("model_type", "CNN")
            confidence = quality.get("confidence", 0.95)
            suggestions = quality.get("suggestions", [])

            if score < 55:
                all_quality_ok = False

            # Score ring fill
            ring_pct = score / 100.0
            ring_color = color
            ring_dash = f"{int(ring_pct * 283)}, 283"

            file_details.append({
                "name": f.name,
                "size": f"{file_size_kb:.1f} KB",
                "pages": estimated_pages,
                "cost": file_cost,
                "cost_per_page": cost_dict["cost_per_page"],
                "data": file_data,
                "quality_score": score,
                "quality_label": label,
                "quality_color": color,
            })

            st.markdown(_clean_html(f"""
                <div class="quality-card">
                    <div class="qc-left">
                        <svg class="quality-ring" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
                            <circle cx="50" cy="50" r="45" fill="none" stroke="{ring_color}" stroke-width="8"
                                stroke-dasharray="{ring_dash}" stroke-dashoffset="70"
                                stroke-linecap="round" transform="rotate(-90 50 50)"/>
                        </svg>
                        <div class="qc-score-overlay">
                            <div class="qc-score-num" style="color:{color};">{score}</div>
                            <div class="qc-score-pct">%</div>
                        </div>
                    </div>
                    <div class="qc-mid">
                        <div class="qc-filename">{f.name}</div>
                        <div class="qc-meta">{estimated_pages} pages • {file_size_kb:.0f} KB • {global_copies} copies</div>
                        <span class="qc-badge" style="background:{color}22;color:{color};border:1px solid {color}44;">
                            {label} — {category}
                        </span>
                        <div class="qc-rec">
                            {'✅' if score >= 75 else '⚠️'} {recommendation}
                        </div>
                        {''.join(f'<div class="qc-sug">• {s}</div>' for s in suggestions[:2])}
                    </div>
                    <div class="qc-right">
                        <div class="qc-cost">₹{file_cost:.2f}</div>
                        <div class="qc-model">🔬 {model_type}</div>
                        <div class="qc-conf">Confidence: {int(confidence*100)}%</div>
                    </div>
                </div>
                """), unsafe_allow_html=True)

    # Batch cost summary
    st.markdown(_clean_html(f"""
        <div class="cost-display">
            <div class="cost-label">Total Estimate — {len(uploaded_files)} Document(s)</div>
            <div class="cost-value">₹{total_batch_cost:.2f}</div>
        </div>
        """), unsafe_allow_html=True)

    if not all_quality_ok:
        st.warning("⚠️ One or more documents have low quality scores. Consider re-uploading higher quality files for best print output.")

    # ── SECTION 3: Smart Printer Selection ────────────────────────────────
    st.markdown(_clean_html('<div class="section-title" style="margin-top:1.5rem;">🖨️ Smart Printer Selection</div>'), unsafe_allow_html=True)

    printers = get_all_printers()
    if not printers:
        st.error("No printers configured in database.")
        return

    # Build printer data with live metrics
    printer_data = []
    for p in printers:
        p_id = p.get("id")
        jobs = get_print_jobs_for_printer(p_id)
        queue_len = sum(1 for j in jobs if j.get("status") in ["Queued", "Printing"])
        curr_job = next((j for j in jobs if j.get("status") == "Printing"), None)
        curr_job_name = (curr_job.get("document_name", "")[:15] + "...") if curr_job else "None (Idle)"
        wait_info = predict_wait_time(
            queue_length=queue_len,
            pages=total_batch_pages,
            copies=1,
            printer_speed_ppm=p.get("ppm", 30),
            priority_flag=priority,
        )
        wait_min = wait_info["estimated_wait_minutes"]
        comp_time = (datetime.now() + timedelta(minutes=wait_min)).strftime("%H:%M")

        printer_data.append({
            **p,
            "queue_length": queue_len,
            "curr_job_name": curr_job_name,
            "wait_min": wait_min,
            "comp_time": comp_time,
            "ppm": p.get("ppm", 30),
        })

    # AI Recommendation engine
    rec_result = recommend_printers(
        job_pages=total_batch_pages,
        job_copies=global_copies,
        color_required=is_color,
        available_printers=[p for p in printer_data if p.get("status") == "Online"],
    )
    recommended_id = rec_result.get("best_printer", {}).get("printer_id") if rec_result else None
    fastest_id     = rec_result.get("fastest_printer", {}).get("printer_id") if rec_result else None
    lowest_wait_id = rec_result.get("lowest_wait_time_printer", {}).get("printer_id") if rec_result else None

    # AI recommendation summary banner
    if recommended_id:
        rec_name = next((p["name"] for p in printer_data if p["id"] == recommended_id), "—")
        rec_wait  = next((p["wait_min"] for p in printer_data if p["id"] == recommended_id), 0)
        st.markdown(_clean_html(f"""
            <div class="rec-banner">
                <div class="rec-banner-icon">🤖</div>
                <div>
                    <div class="rec-banner-title">AI Recommendation Engine</div>
                    <div class="rec-banner-sub">
                        Best overall: <strong>{rec_name}</strong> — Est. wait: <strong>{rec_wait} min</strong>
                    </div>
                </div>
            </div>
            """), unsafe_allow_html=True)

    # Default selected printer
    selected_printer_id = st.session_state.get("selected_printer_id")
    if not selected_printer_id:
        if recommended_id:
            selected_printer_id = recommended_id
        else:
            online_printers = [p for p in printer_data if p.get("status") == "Online"]
            if online_printers:
                selected_printer_id = online_printers[0]["id"]
        st.session_state["selected_printer_id"] = selected_printer_id

    selected_printer_name = "None"
    selected_wait_time = 0

    # Printer cards — 3 per row
    chunk_size = 3
    printer_chunks = [printer_data[i:i+chunk_size] for i in range(0, len(printer_data), chunk_size)]

    for chunk in printer_chunks:
        cols = st.columns(len(chunk))
        for col, p in zip(cols, chunk):
            p_id     = p["id"]
            p_name   = p.get("name", "Printer")
            p_status = p.get("status", "Offline")
            p_loc    = p.get("location", "Unknown")
            queue_len = p["queue_length"]
            wait_min  = p["wait_min"]
            comp_time = p["comp_time"]
            curr_job_name = p["curr_job_name"]
            ppm = p["ppm"]
            toner = p.get("toner_level", 0)

            is_selected = (p_id == selected_printer_id)
            if is_selected:
                selected_printer_name = p_name
                selected_wait_time = wait_min

            # Status colors
            if p_status == "Online" and queue_len == 0:
                status_color = "#10b981"
                status_dot   = "🟢"
                status_label = "Online — Idle"
            elif p_status == "Online" and queue_len > 0:
                status_color = "#f59e0b"
                status_dot   = "🟡"
                status_label = f"Online — {queue_len} in queue"
            elif p_status == "Maintenance":
                status_color = "#f59e0b"
                status_dot   = "🔧"
                status_label = "Maintenance"
            else:
                status_color = "#ef4444"
                status_dot   = "🔴"
                status_label = "Offline"

            # Recommendation badges
            badges = ""
            if p_id == recommended_id:
                badges += '<span class="badge-rec">⭐ Best Choice</span>'
            if p_id == fastest_id and fastest_id != recommended_id:
                badges += '<span class="badge-fast">⚡ Fastest</span>'
            if p_id == lowest_wait_id and lowest_wait_id != recommended_id:
                badges += '<span class="badge-wait">⏱ Least Wait</span>'

            # Toner bar
            toner_color = "#10b981" if toner > 50 else "#f59e0b" if toner > 20 else "#ef4444"

            # Active border
            card_border = f"2px solid {status_color};" if is_selected else "1px solid rgba(255,255,255,0.08);"
            card_glow   = f"box-shadow:0 0 18px {status_color}30;" if is_selected else ""

            with col:
                st.markdown(_clean_html(f"""
                    <div class="printer-card" style="border:{card_border}{card_glow}">
                        <div class="p-title-row">
                            <span class="p-name-label">{p_name[:18]}</span>
                            <span style="color:{status_color};font-size:0.72rem;font-weight:700;">{status_dot} {p_status}</span>
                        </div>
                        <div class="p-loc-label">📍 {p_loc[:25]}</div>
                        <div class="p-status-chip" style="background:{status_color}18;color:{status_color};border:1px solid {status_color}33;">
                            {status_label}
                        </div>
                        {('<div class="p-badges">' + badges + '</div>') if badges else ''}
                        <div class="p-divider"></div>
                        <div class="p-metric-row">
                            <span class="pm-lbl">Queue Size</span>
                            <span class="pm-val">{queue_len} Jobs</span>
                        </div>
                        <div class="p-metric-row">
                            <span class="pm-lbl">Speed</span>
                            <span class="pm-val">{ppm} ppm</span>
                        </div>
                        <div class="p-metric-row">
                            <span class="pm-lbl">Current Job</span>
                            <span class="pm-val">{curr_job_name}</span>
                        </div>
                        <div class="p-metric-row">
                            <span class="pm-lbl">Est. Wait</span>
                            <span class="pm-val" style="color:#f59e0b;">{wait_min} min</span>
                        </div>
                        <div class="p-metric-row">
                            <span class="pm-lbl">Est. Done</span>
                            <span class="pm-val" style="color:#06b6d4;">{comp_time}</span>
                        </div>
                        <div class="p-toner-row">
                            <span class="pm-lbl">Toner</span>
                            <div class="p-toner-bar-bg">
                                <div class="p-toner-bar-fill" style="width:{toner}%;background:{toner_color};"></div>
                            </div>
                            <span style="font-size:0.7rem;color:{toner_color};font-weight:700;">{toner}%</span>
                        </div>
                        {'<div class="p-selected-badge">✓ Selected</div>' if is_selected else ''}
                    </div>
                    """), unsafe_allow_html=True)

                if p_status not in ("Online",):
                    st.button("🚫 Unavailable", key=f"sel_p_{p_id}", disabled=True, use_container_width=True)
                else:
                    label_btn = "✓ Selected" if is_selected else "Select Printer"
                    btn_type = "primary" if is_selected else "secondary"
                    if st.button(label_btn, key=f"sel_p_{p_id}", type=btn_type, use_container_width=True):
                        st.session_state["selected_printer_id"] = p_id
                        st.rerun()

    # ── SECTION 4: Wait Time Summary ─────────────────────────────────────
    if selected_printer_id:
        sel_p = next((p for p in printer_data if p["id"] == selected_printer_id), None)
        if sel_p:
            wait_info = predict_wait_time(
                queue_length=sel_p["queue_length"],
                pages=total_batch_pages,
                copies=global_copies,
                printer_speed_ppm=sel_p["ppm"],
                priority_flag=priority,
            )
            est_start = datetime.now().strftime("%H:%M")
            est_done  = (datetime.now() + timedelta(minutes=wait_info["estimated_wait_minutes"])).strftime("%H:%M")

            st.markdown(_clean_html(f"""
                <div class="wait-panel">
                    <div class="wait-panel-title">⏱ Wait Time Prediction — {sel_p['name']}</div>
                    <div class="wait-panel-grid">
                        <div class="wait-stat">
                            <div class="ws-val">{wait_info['estimated_wait_minutes']} min</div>
                            <div class="ws-lbl">Estimated Wait</div>
                        </div>
                        <div class="wait-stat">
                            <div class="ws-val">{est_start}</div>
                            <div class="ws-lbl">Est. Start Time</div>
                        </div>
                        <div class="wait-stat">
                            <div class="ws-val">{est_done}</div>
                            <div class="ws-lbl">Est. Completion</div>
                        </div>
                        <div class="wait-stat">
                            <div class="ws-val">{sel_p['queue_length']}</div>
                            <div class="ws-lbl">Jobs Ahead</div>
                        </div>
                    </div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);margin-top:8px;text-align:right;">
                        Model: {wait_info['model_used']} • Confidence: {int(wait_info['confidence']*100)}%
                    </div>
                </div>
                """), unsafe_allow_html=True)

    # ── SECTION 5: Checkout Button ────────────────────────────────────────
    with st.container():
        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
        if st.button("💳 Proceed to Checkout", use_container_width=True, key="proceed_btn"):
            try:
                selected_p_id = st.session_state.get("selected_printer_id")
                if not selected_p_id:
                    st.error("Please select a printer node.")
                    return

                upload_dir = "uploads"
                os.makedirs(upload_dir, exist_ok=True)
                qr_dir = "qrcodes"
                os.makedirs(qr_dir, exist_ok=True)

                write_log("UPLOAD_LOG",
                    f"Checkout initiated: {len(file_details)} files, "
                    f"₹{total_batch_cost:.2f}, printer_id={selected_p_id}")

                batch_print_id = generate_print_id()
                job_ids = []

                for f_detail in file_details:
                    job_print_id = generate_print_id()
                    file_path = os.path.join(upload_dir, f"{job_print_id}_{f_detail['name']}")
                    with open(file_path, "wb") as fh:
                        fh.write(f_detail["data"])

                    job_qr_path = os.path.join(qr_dir, f"{job_print_id}.png")
                    qr_text = f"SmartPrint|Job|{job_print_id}|{f_detail['name']}|{username}"
                    generate_qr_code(qr_text, job_qr_path)

                    job_dict = create_print_job(
                        user_id=user_id,
                        document_name=f_detail["name"],
                        file_path=file_path,
                        print_id=job_print_id,
                        copies=global_copies,
                        color_mode=color_mode_db,
                        duplex=is_duplex,
                        page_range="All",
                        paper_size="A4",
                        priority=priority_str,
                        total_pages=f_detail["pages"],
                        cost_per_page=f_detail["cost_per_page"],
                        total_cost=f_detail["cost"],
                        qr_code_path=job_qr_path,
                        printer_id=selected_p_id,
                        estimated_wait_time=int(selected_wait_time),
                    )
                    job_id = job_dict["id"]
                    job_ids.append(job_id)

                    create_ai_analysis(
                        job_id=job_id,
                        quality_score=float(f_detail["quality_score"]),
                        is_blurry=(f_detail["quality_label"] == "Poor"),
                        is_skewed=False,
                        is_low_quality=(f_detail["quality_score"] < 60),
                        recommendations=f"Quality: {f_detail['quality_label']} ({f_detail['quality_score']}%)",
                    )
                    write_log("JOB_LOG",
                        f"Job created: {job_print_id}, doc={f_detail['name']}, "
                        f"quality={f_detail['quality_score']}%, cost=₹{f_detail['cost']:.2f}")

                batch_qr_path = os.path.join(qr_dir, f"{batch_print_id}.png")
                generate_qr_code(f"SmartPrint|Batch|{batch_print_id}|₹{total_batch_cost:.2f}", batch_qr_path)

                st.session_state["upload_success"]    = True
                st.session_state["upload_batch_id"]   = batch_print_id
                st.session_state["upload_job_ids"]    = job_ids
                st.session_state["upload_cost"]       = total_batch_cost
                st.session_state["upload_qr_path"]    = batch_qr_path
                st.session_state["upload_qr_text"]    = f"SmartPrint|Batch|{batch_print_id}"
                st.rerun()

            except Exception as e:
                write_log("UPLOAD_LOG", "Checkout failure", e)
                st.error(f"Checkout failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Success screen
# ─────────────────────────────────────────────────────────────────────────────

def _show_success_screen():
    batch_id = st.session_state.get("upload_batch_id", "N/A")
    cost     = st.session_state.get("upload_cost", 0)
    job_ids  = st.session_state.get("upload_job_ids", [])

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(_clean_html(f"""
            <div class="success-card">
                <div style="font-size:3.5rem;margin-bottom:12px;">✅</div>
                <div class="success-title">Upload Successful</div>
                <div class="success-subtitle">{len(job_ids)} Document(s) ready for checkout</div>
                <div class="success-detail">
                    <div class="sd-row"><span class="sd-label">Batch ID:</span><span class="sd-value">{batch_id}</span></div>
                    <div class="sd-row"><span class="sd-label">Estimated:</span><span class="sd-value">₹{cost:.2f}</span></div>
                </div>
            </div>
            """), unsafe_allow_html=True)

        qr_path = st.session_state.get("upload_qr_path")
        if qr_path and os.path.exists(qr_path):
            _, img_col, _ = st.columns([1, 2, 1])
            with img_col:
                st.image(qr_path, caption="Scan to track print status", width=180)

        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
        if st.button("💳 Proceed to Checkout Payment", use_container_width=True, key="pay_proceed_btn"):
            st.session_state["current_page"]        = "Payments"
            st.session_state["payment_batch_cost"]  = cost
            st.session_state["payment_job_ids"]     = job_ids
            _clear_upload_state()
            st.rerun()


def _clear_upload_state():
    for key in ["upload_success", "upload_batch_id", "upload_job_ids",
                "upload_cost", "upload_qr_text", "upload_qr_path"]:
        st.session_state.pop(key, None)


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

def _upload_css() -> str:
    return """
    <style>
    .upload-header { text-align:center; padding:20px 0 10px; }
    .upload-icon { font-size:3rem; margin-bottom:8px; }
    .upload-title {
        font-size:2rem; font-weight:800;
        background:linear-gradient(135deg,#00D9FF,#00F5FF);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .upload-subtitle { color:rgba(255,255,255,0.5); font-size:0.95rem; margin-top:4px; }

    .upload-dropzone {
        border:2px dashed rgba(255,255,255,0.15); border-radius:16px;
        padding:30px 20px; text-align:center; background:rgba(255,255,255,0.02);
        margin-top:4px; transition:border-color .25s;
    }
    .upload-dropzone:hover { border-color:#00F5FF; }

    .section-title {
        font-size:1.1rem; font-weight:700; color:rgba(255,255,255,0.85);
        margin:1.5rem 0 10px; text-transform:uppercase; letter-spacing:.5px;
    }

    /* ── AI Banner ── */
    .ai-banner {
        display:flex; align-items:center; gap:12px;
        background:linear-gradient(135deg,rgba(0,217,255,.10),rgba(0,255,170,.10));
        border:1px solid rgba(0,217,255,.25); border-radius:12px;
        padding:12px 18px; margin-bottom:14px;
    }
    .ai-banner-icon { font-size:1.4rem; }
    .ai-banner-text { color:rgba(255,255,255,0.75); font-size:0.88rem; font-weight:500; }

    /* ── Quality Card ── */
    .quality-card {
        display:flex; align-items:flex-start; gap:18px;
        background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
        border-radius:16px; padding:16px 20px; margin-bottom:10px;
        transition:transform .2s, box-shadow .2s;
    }
    .quality-card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,.3); }
    .qc-left { position:relative; flex-shrink:0; width:72px; height:72px; }
    .quality-ring { width:72px; height:72px; }
    .qc-score-overlay {
        position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
        text-align:center; line-height:1;
    }
    .qc-score-num { font-size:1.3rem; font-weight:900; }
    .qc-score-pct { font-size:0.6rem; color:rgba(255,255,255,.4); font-weight:600; }
    .qc-mid { flex:1; }
    .qc-filename { font-size:0.92rem; font-weight:700; color:#fff; margin-bottom:3px; }
    .qc-meta { font-size:0.75rem; color:rgba(255,255,255,.4); margin-bottom:7px; }
    .qc-badge {
        display:inline-block; padding:3px 10px; border-radius:20px;
        font-size:0.72rem; font-weight:700; letter-spacing:.03em; margin-bottom:7px;
    }
    .qc-rec { font-size:0.82rem; color:rgba(255,255,255,.7); margin-bottom:4px; }
    .qc-sug { font-size:0.75rem; color:rgba(255,255,255,.4); }
    .qc-right { text-align:right; min-width:90px; }
    .qc-cost { font-size:1.2rem; font-weight:800; color:#00D9FF; }
    .qc-model { font-size:0.68rem; color:rgba(255,255,255,.35); margin-top:6px; }
    .qc-conf { font-size:0.7rem; color:rgba(255,255,255,.45); }

    /* ── Cost Display ── */
    .cost-display {
        background:linear-gradient(135deg,rgba(0,217,255,.08),rgba(0,255,170,.08));
        border:1px solid rgba(0,217,255,.18); border-radius:14px;
        padding:16px; text-align:center; margin-top:12px;
    }
    .cost-label { color:rgba(255,255,255,.45); font-size:.8rem; text-transform:uppercase; letter-spacing:.8px; font-weight:600; }
    .cost-value {
        font-size:1.8rem; font-weight:800;
        background:linear-gradient(135deg,#00D9FF,#00F5FF);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-top:2px;
    }

    /* ── AI Recommendation Banner ── */
    .rec-banner {
        display:flex; align-items:center; gap:14px;
        background:linear-gradient(135deg,rgba(16,185,129,.10),rgba(6,182,212,.10));
        border:1px solid rgba(16,185,129,.30); border-radius:14px;
        padding:14px 20px; margin-bottom:16px;
    }
    .rec-banner-icon { font-size:1.8rem; }
    .rec-banner-title { font-size:0.95rem; font-weight:700; color:#10b981; }
    .rec-banner-sub { font-size:0.82rem; color:rgba(255,255,255,.6); margin-top:2px; }

    /* ── Printer Cards ── */
    .printer-card {
        background:rgba(255,255,255,0.03);
        border-radius:16px; padding:14px;
        margin-bottom:8px; transition:transform .2s, box-shadow .2s;
        position:relative;
    }
    .printer-card:hover { transform:translateY(-3px); }
    .p-title-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
    .p-name-label { font-weight:700; color:#fff; font-size:0.85rem; }
    .p-loc-label { font-size:0.72rem; color:rgba(255,255,255,.4); margin-bottom:8px; }
    .p-status-chip {
        display:inline-block; padding:3px 10px; border-radius:20px;
        font-size:0.7rem; font-weight:700; margin-bottom:8px;
    }
    .p-badges { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:8px; }
    .badge-rec {
        background:rgba(251,191,36,.12); color:#fbbf24;
        border:1px solid rgba(251,191,36,.30); border-radius:12px;
        padding:2px 8px; font-size:0.68rem; font-weight:700;
    }
    .badge-fast {
        background:rgba(0,217,255,.12); color:#00D9FF;
        border:1px solid rgba(0,217,255,.30); border-radius:12px;
        padding:2px 8px; font-size:0.68rem; font-weight:700;
    }
    .badge-wait {
        background:rgba(6,182,212,.12); color:#22d3ee;
        border:1px solid rgba(6,182,212,.30); border-radius:12px;
        padding:2px 8px; font-size:0.68rem; font-weight:700;
    }
    .p-divider { border-top:1px solid rgba(255,255,255,.05); margin:8px 0; }
    .p-metric-row { display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:4px; }
    .pm-lbl { color:rgba(255,255,255,.45); }
    .pm-val { color:#fff; font-weight:600; }
    .p-toner-row { display:flex; align-items:center; gap:8px; margin-top:8px; font-size:0.72rem; }
    .p-toner-bar-bg { flex:1; height:5px; background:rgba(255,255,255,.08); border-radius:4px; overflow:hidden; }
    .p-toner-bar-fill { height:100%; border-radius:4px; transition:width .5s; }
    .p-selected-badge {
        position:absolute; top:10px; right:10px;
        background:rgba(16,185,129,.15); color:#10b981;
        border:1px solid rgba(16,185,129,.35); border-radius:12px;
        padding:2px 8px; font-size:0.68rem; font-weight:700;
    }

    /* ── Wait Panel ── */
    .wait-panel {
        background:rgba(6,182,212,.06); border:1px solid rgba(6,182,212,.20);
        border-radius:14px; padding:16px 20px; margin-top:14px;
    }
    .wait-panel-title { font-size:0.95rem; font-weight:700; color:#22d3ee; margin-bottom:12px; }
    .wait-panel-grid { display:flex; gap:0; }
    .wait-stat {
        flex:1; text-align:center; padding:8px 4px;
        border-right:1px solid rgba(255,255,255,.06);
    }
    .wait-stat:last-child { border-right:none; }
    .ws-val { font-size:1.3rem; font-weight:800; color:#fff; }
    .ws-lbl { font-size:0.7rem; color:rgba(255,255,255,.4); margin-top:3px; text-transform:uppercase; letter-spacing:.04em; }

    /* ── Success Card ── */
    .success-card {
        background:rgba(255,255,255,.03); border:1px solid rgba(16,185,129,.18);
        border-radius:20px; padding:30px 24px; text-align:center; backdrop-filter:blur(12px);
    }
    .success-title { font-size:1.6rem; font-weight:800; color:#10b981; margin-bottom:4px; }
    .success-subtitle { color:rgba(255,255,255,.5); font-size:0.88rem; margin-bottom:16px; }
    .success-detail { background:rgba(255,255,255,.03); border-radius:10px; padding:12px 18px; display:inline-block; text-align:left; }
    .sd-row { display:flex; gap:10px; padding:2px 0; }
    .sd-label { color:rgba(255,255,255,.45); font-size:.82rem; min-width:70px; }
    .sd-value { color:#fff; font-weight:700; font-size:.88rem; }
    </style>
    """
