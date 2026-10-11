"""Generate a polished 10-slide consolidated version of SiteGuard Capstone Presentation.
Combines all relevant content from the 20-slide deck into exactly 10 high-impact slides.
Saves to both C:\\Users\\HP\\Downloads and the project folder.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

DEST_DOWNLOADS = Path(r"C:\Users\HP\Downloads\SiteGuard_Capstone_10Slides.pptx")
DEST_PROJECT   = Path(r"d:\projects\MDM capstone\SiteGuard_Capstone_10Slides.pptx")

# ── Color Palette (Matching Original Architecture Theme) ─────────────────────
BG_LIGHT       = RGBColor(243, 239, 230)  # #F3EFE6 (Warm Architect Cream)
CARD_BG        = RGBColor(251, 249, 244)  # #FBF9F4 (Crisp Card Surface)
CARD_BORDER    = RGBColor(226, 220, 206)  # #E2DCCE (Card Outline)
ACCENT_AMBER   = RGBColor(245, 197, 24)   # #F5C518 (Safety Amber / Gold)
ACCENT_DARK    = RGBColor(26, 32, 44)     # #1A202C (Charcoal Primary Text)
TEXT_MUTED     = RGBColor(100, 116, 139)  # #64748B (Slate Secondary Text)
ACCENT_GREEN   = RGBColor(16, 185, 129)   # #10B981 (Success Green)
ACCENT_RED     = RGBColor(239, 68, 68)    # #EF4444 (Alert Red)
ACCENT_CYAN    = RGBColor(14, 165, 233)   # #0EA5E9 (Tech Cyan)
BANNER_BG      = RGBColor(15, 23, 42)     # #0F172A (Deep Dark Accent)


def build_10_slide_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color=BG_LIGHT):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, number: str, category: str, main_title: str):
        # Category + Number Badge
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf = cat_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = f"{number} · {category.upper()}"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(180, 130, 10)

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.6))
        tf2 = title_box.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
        p2 = tf2.paragraphs[0]
        p2.text = main_title
        p2.font.size = Pt(22)
        p2.font.bold = True
        p2.font.color.rgb = ACCENT_DARK

        # Top Right SiteGuard Branding
        brand_box = slide.shapes.add_textbox(Inches(10.5), Inches(0.4), Inches(2.0), Inches(0.4))
        tf_b = brand_box.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = f"SITEGUARD · {number}"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = TEXT_MUTED
        p_b.alignment = PP_ALIGN.RIGHT

    def add_card(slide, left, top, width, height, title: str = "", accent_color=ACCENT_DARK, fill_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = fill_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)

        if title:
            tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.2), Inches(width - 0.5), Inches(0.45))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = accent_color

        return card

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 1: Title Slide (Original Slide 1)
    # ══════════════════════════════════════════════════════════════════════════
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, BANNER_BG)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(0.18), Inches(3.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_AMBER
    bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.4), Inches(1.6), Inches(10.5), Inches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "MDM CAPSTONE · AI + IOT"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_AMBER

    p1 = tf.add_paragraph()
    p1.text = "SITEGUARD"
    p1.font.size = Pt(48)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(248, 250, 252)

    p2 = tf.add_paragraph()
    p2.text = "AI-Based Construction Site Worker Safety Monitoring System"
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = RGBColor(56, 189, 248)

    p3 = tf.add_paragraph()
    p3.text = "\nReal-Time Edge Ingestion • YOLOv8n PPE Detection • BoT-SORT Deep Re-ID • Temporal Hysteresis Rule Engine"
    p3.font.size = Pt(13.5)
    p3.font.color.rgb = RGBColor(148, 163, 184)

    # Tech badges row
    badges = ["ESP32-CAM (5 FPS)", "YOLOv8n (640x640)", "BoT-SORT Re-ID", "70/30 Hysteresis", "SQLite WAL Mode", "WebSocket Dashboard"]
    badge_y = 5.8
    for i, b in enumerate(badges):
        bx = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.4 + i * 1.8), Inches(badge_y), Inches(1.68), Inches(0.42))
        bx.fill.solid()
        bx.fill.fore_color.rgb = RGBColor(30, 41, 59)
        bx.line.color.rgb = RGBColor(51, 65, 85)
        bx_tf = bx.text_frame
        bx_tf.margin_top = bx_tf.margin_bottom = bx_tf.margin_left = bx_tf.margin_right = 0
        p = bx_tf.paragraphs[0]
        p.text = b
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = RGBColor(241, 245, 249)
        p.alignment = PP_ALIGN.CENTER

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 2: Problem Statement & Project Objectives (Original Slides 2 + 3)
    # ══════════════════════════════════════════════════════════════════════════
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "02", "Context & Strategy", "The Problem & Core Project Objectives")

    # Left: The Problem
    add_card(s2, 0.8, 1.5, 5.6, 5.4, "Construction Safety Challenges", RGBColor(180, 50, 50))
    tb = s2.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True

    # Big stat callout inside
    stat_box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.05), Inches(2.1), Inches(5.1), Inches(0.85))
    stat_box.fill.solid()
    stat_box.fill.fore_color.rgb = ACCENT_AMBER
    stat_box.line.fill.background()
    s_tf = stat_box.text_frame
    s_p = s_tf.paragraphs[0]
    s_p.text = "20%+ OF ALL WORKPLACE FATALITIES OCCUR IN CONSTRUCTION"
    s_p.font.size = Pt(12)
    s_p.font.bold = True
    s_p.font.color.rgb = BANNER_BG
    s_p2 = s_tf.add_paragraph()
    s_p2.text = "Missing hardhats & safety vests is the #1 cited OSHA violation nationwide."
    s_p2.font.size = Pt(10.5)
    s_p2.font.color.rgb = BANNER_BG

    prob_tb = s2.shapes.add_textbox(Inches(1.05), Inches(3.1), Inches(5.1), Inches(3.6))
    p_tf = prob_tb.text_frame
    p_tf.word_wrap = True
    probs = [
        ("Low PPE Compliance", "Workers frequently remove helmets and vests in unsupervised zones when no officer is present."),
        ("Monitoring Fatigue", "Safety supervisors cannot watch multiple live camera feeds continuously; human lapses occur."),
        ("False-Alarm Fatigue", "Raw single-frame detectors flicker heavily on momentary occlusion and noise, causing alert dismissal."),
        ("Machinery Blind Spots", "Ground workers cross paths with excavators and cranes without spatial danger tracking.")
    ]
    for t, d in probs:
        p = p_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: Project Objectives
    add_card(s2, 6.8, 1.5, 5.7, 5.4, "Five Core Objectives", RGBColor(16, 120, 80))
    obj_tb = s2.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.6))
    o_tf = obj_tb.text_frame
    o_tf.word_wrap = True
    objs = [
        ("01. Edge Video Ingestion", "Stream low-latency QVGA/VGA frames from wireless ESP32-CAM nodes over Wi-Fi at 5 FPS pacing."),
        ("02. Accurate PPE Attribution", "Simultaneous detection of workers and safety gear with strict bounding-box containment (IoU >= 0.50)."),
        ("03. Stable Identity via Re-ID", "Keep worker IDs consistent through visual occlusions and intersecting paths using BoT-SORT appearance vectors."),
        ("04. Zero Alert Flapping", "Confirm violations only when missing in >=70% of frames over a 10s window (clear at <=30%)."),
        ("05. Real-Time Operations", "Instant WebSocket alert broadcast, evidence JPEG snapshots, and SQLite WAL database audit logging.")
    ]
    for t, d in objs:
        p = o_tf.add_paragraph()
        p.text = f"✔ {t}\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(16, 120, 80)
        r = p.add_run()
        r.text = f"   {d}\n"
        r.font.bold = False
        r.font.size = Pt(11)
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 3: System Features & End-to-End Pipeline Architecture (Slides 4 + 5)
    # ══════════════════════════════════════════════════════════════════════════
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "03", "System Design", "Core Features & 8-Stage End-to-End Architecture")

    # Left: Features Summary (Original Slide 4)
    add_card(s3, 0.8, 1.5, 4.5, 5.4, "Key System Capabilities", ACCENT_DARK)
    f_tb = s3.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(4.1), Inches(4.6))
    f_tf = f_tb.text_frame
    f_tf.word_wrap = True
    feats = [
        ("Multi-Camera Ingestion", "Raw JPEG HTTP POST from wireless ESP32-CAMs & webcams."),
        ("Domain PPE Detection", "Person, Hardhat, Vest, Mask & their 'NO-' violation states."),
        ("Tracking & Re-ID", "BoT-SORT appearance embeddings (ByteTrack supported)."),
        ("Spatial Containment", ">=50% box overlap ties gear strictly to wearer body."),
        ("Temporal Hysteresis", "10s window, 70% confirm / 30% clear eliminates flickering."),
        ("SQLite WAL Engine", "High-concurrency, non-blocking ACID incident logging."),
        ("WebSocket Hub", "Real-time alert dispatch to web dashboard in sub-50 ms."),
        ("Diagnostics & Telemetry", "ESP32 RSSI, heap, FPS tracking; offline after 15s.")
    ]
    for t, d in feats:
        p = f_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: 8-Stage Pipeline (Original Slide 5)
    add_card(s3, 5.6, 1.5, 6.9, 5.4, "8-Stage Frame Dataflow Pipeline", RGBColor(14, 110, 180))
    stages = [
        ("1. Ingestion", "ESP32-CAM posts raw JPEG @ 5 FPS via HTTP POST", "routes/camera.py"),
        ("2. Preprocessing", "BGR to LAB, CLAHE on L channel (<4.2 ms), Letterbox 640x640", "preprocessor.py"),
        ("3. Detection", "YOLOv8n finds Person, PPE worn & missing, and machinery", "inference.py"),
        ("4. Re-ID Tracking", "BoT-SORT preserves worker track IDs across visual occlusions", "botsort_reid.yaml"),
        ("5. Association", "Containment algorithm assigns gear strictly to wearer box", "inference.py"),
        ("6. Safety Engine", "10s sliding window (70% confirm / 30% clear) suppresses noise", "safety_engine.py"),
        ("7. Persistence", "Annotated snapshot saved; incident logged to SQLite WAL", "event_manager.py"),
        ("8. Web Dashboard", "Live WebSockets push compliance status & telemetry to UI", "websocket_hub.py")
    ]
    for idx, (st, sd, sc) in enumerate(stages):
        row = idx // 2
        col = idx % 2
        bx = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.8 + col * 3.35), Inches(2.1 + row * 1.15), Inches(3.2), Inches(1.0))
        bx.fill.solid()
        bx.fill.fore_color.rgb = RGBColor(245, 247, 250)
        bx.line.color.rgb = RGBColor(210, 220, 230)
        btf = bx.text_frame
        btf.margin_top = btf.margin_bottom = btf.margin_left = btf.margin_right = 0
        p = btf.paragraphs[0]
        p.text = st
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(14, 110, 180)
        p2 = btf.add_paragraph()
        p2.text = sd
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = ACCENT_DARK
        p3 = btf.add_paragraph()
        p3.text = f"[{sc}]"
        p3.font.size = Pt(8.5)
        p3.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 4: Edge IoT Hardware & Embedded Firmware (Slides 6 + 7)
    # ══════════════════════════════════════════════════════════════════════════
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "04", "Edge IoT Tier", "ESP32-CAM Hardware Architecture & Embedded Firmware")

    # Left: Hardware Specs (Slide 6)
    add_card(s4, 0.8, 1.5, 5.6, 5.4, "AI-Thinker ESP32-CAM Node", RGBColor(180, 120, 10))
    h_tb = s4.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    h_tf = h_tb.text_frame
    h_tf.word_wrap = True
    h_specs = [
        ("Microcontroller", "Dual-core Xtensa 32-bit LX6 @ 240 MHz (AI-Thinker ESP32)."),
        ("Camera Sensor", "Omnivision OV2640 2-Megapixel CMOS sensor with hardware JPEG encoding."),
        ("Memory Subsystem", "520 KB internal SRAM + 4 MB external PSRAM for double buffering."),
        ("Wireless Connectivity", "Integrated 802.11 b/g/n Wi-Fi (2.4 GHz) link to Host Server."),
        ("Host Machine Profile", "AMD Ryzen 5 5625U CPU (integrated Radeon Graphics), running FastAPI + SQLite."),
        ("Power Requirements", "5V DC stabilized external power supply (common ground).")
    ]
    for t, d in h_specs:
        p = h_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: Firmware & Networking (Slide 7)
    add_card(s4, 6.8, 1.5, 5.7, 5.4, "Firmware & HTTP Ingestion (velxio.cpp)", RGBColor(14, 110, 180))
    fw_tb = s4.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.5))
    fw_tf = fw_tb.text_frame
    fw_tf.word_wrap = True
    fw_specs = [
        ("Paced Frame Interval", "5 FPS (200 ms loop pacing, counting transmission latency)."),
        ("Resolution & Compression", "QVGA (320x240) JPEG at quality factor 12 (crisp, small payload)."),
        ("PSRAM Double Buffering", "config.fb_count = 2 in PSRAM with CAMERA_GRAB_LATEST: captures next frame while uploading current frame."),
        ("HTTP Socket Reuse", "http.setReuse(true) keep-alive skips fresh TCP handshake per frame."),
        ("Self-Healing Telemetry", "Camera init retries every 2s on failure; Wi-Fi auto-reconnects on RF drop."),
        ("Heartbeat Telemetry", "Reports device_id, Wi-Fi RSSI, free heap, and uptime to /api/camera/heartbeat.")
    ]
    for t, d in fw_specs:
        p = fw_tf.add_paragraph()
        p.text = f"⚡ {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = RGBColor(14, 110, 180)
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 5: Image Preprocessing & YOLOv8n Detection (Slides 8 + 9)
    # ══════════════════════════════════════════════════════════════════════════
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "05", "Computer Vision Tier", "CLAHE Contrast Enhancement & YOLOv8n Gated Detection")

    # Left: CLAHE Preprocessing (Slide 8)
    add_card(s5, 0.8, 1.5, 5.6, 5.4, "Luminance-Preserving CLAHE", RGBColor(14, 110, 180))
    c_tb = s5.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    c_tf = c_tb.text_frame
    c_tf.word_wrap = True
    c_steps = [
        ("1. Buffer Decoding", "cv2.imdecode parses incoming JPEG bytes into a standard BGR NumPy array."),
        ("2. BGR to CIE LAB", "Separates Luminance (L) from chromatic channels (A and B). This preserves vibrant PPE colors (orange/neon yellow) without color shift."),
        ("3. Adaptive CLAHE on L", "clipLimit = 2.0, tileGridSize = (8, 8). Boosts local contrast in harsh shadows, backlit scaffolding, and dawn/dusk lighting while capping noise amplification."),
        ("4. Letterboxing", "Converted back to BGR; aspect-ratio padded to 640x640 px for neural input."),
        ("Benchmark Speed", "<4.2 ms execution per frame on Ryzen 5 CPU; zero ingestion bottleneck.")
    ]
    for t, d in c_steps:
        p = c_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: YOLOv8n Detection & Gating (Slide 9)
    add_card(s5, 6.8, 1.5, 5.7, 5.4, "YOLOv8n & Asymmetric Confidence Gates", RGBColor(180, 120, 10))
    y_tb = s5.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.5))
    y_tf = y_tb.text_frame
    y_tf.word_wrap = True
    y_points = [
        ("Architecture", "Ultralytics YOLOv8n (Nano) anchor-free single-stage detector (~6.2 MB)."),
        ("10 Active Classes", "Person, Hardhat, NO-Hardhat, Vest, NO-Vest, Mask, NO-Mask, Cone, machinery, vehicle."),
        ("Tighter NMS IoU (0.40)", "Eliminates duplicate overlapping boxes (Ultralytics default is 0.70)."),
        ("Person Gate: 0.35", "Low threshold ensures workers are never missed even under distance or occlusion."),
        ("Worn PPE Gate: 0.40", "Hardhat, Safety Vest, Mask: balanced threshold for worn gear."),
        ("Violation Gate: 0.50", "NO-Hardhat, NO-Safety Vest, NO-Mask: higher threshold suppresses false alarms.")
    ]
    for t, d in y_points:
        p = y_tf.add_paragraph()
        p.text = f"🎯 {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = RGBColor(180, 120, 10)
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 6: Tracking (BoT-SORT Deep Re-ID) & Spatial Containment (Slides 10 + 11)
    # ══════════════════════════════════════════════════════════════════════════
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "06", "Association & Identity", "BoT-SORT Deep Re-ID & Spatial Containment Association")

    # Left: BoT-SORT Re-ID (Slide 10)
    add_card(s6, 0.8, 1.5, 5.6, 5.4, "BoT-SORT Tracking with Deep Re-ID", RGBColor(180, 120, 10))
    r_tb = s6.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    r_tf = r_tb.text_frame
    r_tf.word_wrap = True
    reids = [
        ("The Limitation of Motion-Only", "Kalman filter trackers (ByteTrack / SORT) lose identity when workers cross paths or stop moving behind scaffolding."),
        ("Deep Visual Embeddings", "with_reid: True extracts deep appearance vectors for every detected worker box."),
        ("Global Motion Compensation", "gmc_method: sparseOptFlow cancels camera vibrations and wind movement."),
        ("Appearance Threshold (0.75)", "High cosine similarity bar prevents false ID swaps between workers wearing similar gear."),
        ("Track Buffer (45 frames)", "Maintains lost tracks for >9 seconds at 5 FPS to reconnect re-emerging workers.")
    ]
    for t, d in reids:
        p = r_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: Spatial Containment (Slide 11)
    add_card(s6, 6.8, 1.5, 5.7, 5.4, "Bounding Box Containment Matching", RGBColor(16, 120, 80))
    cnt_tb = s6.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.5))
    cnt_tf = cnt_tb.text_frame
    cnt_tf.word_wrap = True

    # Containment Formula Card
    form_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.05), Inches(2.1), Inches(5.2), Inches(0.85))
    form_box.fill.solid()
    form_box.fill.fore_color.rgb = RGBColor(235, 245, 240)
    form_box.line.color.rgb = RGBColor(180, 220, 200)
    f_tf = form_box.text_frame
    f_p = f_tf.paragraphs[0]
    f_p.text = "CONTAINMENT(B_PPE, B_Person) = Area(B_PPE ∩ B_Person) / Area(B_PPE)"
    f_p.font.size = Pt(10)
    f_p.font.bold = True
    f_p.font.color.rgb = RGBColor(16, 120, 80)
    f_p2 = f_tf.add_paragraph()
    f_p2.text = "Threshold: >= 0.50 (at least 50% of PPE box must lie inside Person box)"
    f_p2.font.size = Pt(9.5)
    f_p2.font.color.rgb = ACCENT_DARK

    cnt_text_tb = s6.shapes.add_textbox(Inches(7.05), Inches(3.1), Inches(5.2), Inches(3.6))
    ct_tf = cnt_text_tb.text_frame
    ct_tf.word_wrap = True
    cnts = [
        ("Multi-Worker Disambiguation", "When workers stand side-by-side, each PPE item belongs strictly to the worker bounding box that contains it."),
        ("Floor / Scaffold Drop", "Loose PPE lying on the ground or scaffold matches nobody and is automatically discarded."),
        ("Conflict Resolution", "If both Hardhat and NO-Hardhat land on the same worker, the higher confidence score wins."),
        ("Atomic Worker Checklist", "Produces a per-worker checklist bound to the track_id: {'helmet': ('ok', 0.82), 'vest': ('missing', 0.74)}.")
    ]
    for t, d in cnts:
        p = ct_tf.add_paragraph()
        p.text = f"✔ {t}: "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(16, 120, 80)
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 7: Safety Rule Engine & Live Incident Dispatch (Slides 12 + 13 + 14)
    # ══════════════════════════════════════════════════════════════════════════
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "07", "Safety Engine", "Dual-Threshold Temporal Hysteresis & Incident Dispatch")

    # Left: Temporal Hysteresis (Slide 12)
    add_card(s7, 0.8, 1.5, 5.6, 5.4, "10-Second Hysteresis Rule Engine", RGBColor(180, 50, 50))
    h_tb = s7.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    h_tf = h_tb.text_frame
    h_tf.word_wrap = True
    h_rules = [
        ("Sliding Window Buffer", "Tracks each worker's PPE observations over a 10.0-second sliding window (requires >=3 frames)."),
        ("Confirmation Threshold (70%)", "An item is confirmed missing only when absent in >=70% of frames over the full window."),
        ("Clearance Threshold (30%)", "A violation is cleared only once missing share drops to <=30%."),
        ("Zero Alert Flapping", "The 40% hysteresis gap prevents alerts from toggling on and off during momentary head turns or occlusion."),
        ("Single-Episode Incidents", "Raises exactly ONE incident when an episode starts; new missing items update it; no duplicate alerts.")
    ]
    for t, d in h_rules:
        p = h_tf.add_paragraph()
        p.text = f"• {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = ACCENT_DARK
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # Right: Incident Logging & Telemetry (Slide 13 + 14)
    add_card(s7, 6.8, 1.5, 5.7, 5.4, "Incident Lifecycle & Dispatch", RGBColor(14, 110, 180))
    inc_tb = s7.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.5))
    inc_tf = inc_tb.text_frame
    inc_tf.word_wrap = True
    inc_points = [
        ("Evidence Snapshot Saving", "Saves annotated JPEG evidence snapshot to data/evidence/ immediately upon violation confirmation."),
        ("Non-Blocking SQLite WAL", "Uses PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL for concurrent ACID logging."),
        ("Severity Tiers", "Helmet missing: HIGH | Vest missing: HIGH | Mask missing: MEDIUM."),
        ("WebSocket Real-Time Push", "Broadcasts 'INCIDENT_ALERT' payload to all connected dashboard sessions in sub-50 ms."),
        ("Dynamic Parameter Overrides", "Every threshold is configurable via SITEGUARD_* environment variables or live dashboard sliders (no server reboot).")
    ]
    for t, d in inc_points:
        p = inc_tf.add_paragraph()
        p.text = f"🔔 {t}: "
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = RGBColor(14, 110, 180)
        r = p.add_run()
        r.text = d
        r.font.bold = False
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 8: Evaluation & Safety Reliability Scorecard (Slide 15)
    # ══════════════════════════════════════════════════════════════════════════
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "08", "System Validity", "Safety Reliability Scorecard & Empirical Benchmarks")

    # Top Callout Card
    top_c = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(11.7), Inches(1.3))
    top_c.fill.solid()
    top_c.fill.fore_color.rgb = RGBColor(235, 248, 240)
    top_c.line.color.rgb = RGBColor(180, 225, 200)
    t_tf = top_c.text_frame
    p1 = t_tf.paragraphs[0]
    p1.text = "OVERALL SAFETY RELIABILITY SCORE: 91.25 / 100  (GRADE A+)"
    p1.font.size = Pt(18)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(16, 120, 80)
    p2 = t_tf.add_paragraph()
    p2.text = "Composite Formulation: Score = (0.35 · S_det) + (0.25 · S_lat) + (0.20 · S_up) + (0.20 · S_dup)"
    p2.font.size = Pt(12)
    p2.font.color.rgb = ACCENT_DARK

    # 4 Pillar Breakdown Cards
    pillars = [
        ("Detection Reliability (35%)", "85.0 / 100", "Worker & PPE precision/recall on complex site video footage.", RGBColor(14, 110, 180)),
        ("Latency Performance (25%)", "90.0 / 100", "Average inference latency 48.2 ms on consumer Ryzen 5 CPU.", RGBColor(180, 120, 10)),
        ("System Uptime (20%)", "95.0 / 100", "ESP32 node heartbeat continuity and automatic recovery.", RGBColor(16, 120, 80)),
        ("Duplicate Suppression (20%)", "100.0 / 100", "Single-incident episode state management eliminates noise.", RGBColor(180, 50, 50))
    ]
    for idx, (p_title, p_score, p_desc, p_col) in enumerate(pillars):
        x = 0.8 + idx * 2.95
        card = add_card(s8, x, 3.1, 2.85, 2.4, p_title, p_col)
        tb = s8.shapes.add_textbox(Inches(x + 0.2), Inches(3.7), Inches(2.45), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = p_score
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = p_col
        p2 = tf.add_paragraph()
        p2.text = f"\n{p_desc}"
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = TEXT_MUTED

    # Bottom Benchmark Summary
    bot_c = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.75), Inches(11.7), Inches(1.15))
    bot_c.fill.solid()
    bot_c.fill.fore_color.rgb = CARD_BG
    bot_c.line.color.rgb = CARD_BORDER
    b_tf = bot_c.text_frame
    bp = b_tf.paragraphs[0]
    bp.text = "Load Benchmark Results (tools/benchmark_system.py):"
    bp.font.bold = True
    bp.font.size = Pt(12)
    bp.font.color.rgb = ACCENT_DARK
    bp2 = b_tf.add_paragraph()
    bp2.text = "Tested with 2–4 concurrent cameras streaming @ 5 FPS. Async queue prevented handler blocking with 0 dropped frames and sub-100 ms end-to-end latency."
    bp2.font.size = Pt(11)
    bp2.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 9: Scientific Research Backing (15 Papers) (Slide 16)
    # ══════════════════════════════════════════════════════════════════════════
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "09", "Literature Justification", "Benchmark Matrix: 15 Research Papers Backing SiteGuard")

    # Table of 15 papers (Consolidated into 2 columns of cards)
    add_card(s9, 0.8, 1.5, 5.6, 5.4, "Built Capabilities (11 Papers)", RGBColor(16, 120, 80))
    p1_tb = s9.shapes.add_textbox(Inches(1.0), Inches(2.05), Inches(5.2), Inches(4.7))
    p1_tf = p1_tb.text_frame
    p1_tf.word_wrap = True
    built_papers = [
        ("BoT-SORT (Aharon 2022)", "Re-ID appearance embeddings + GMC tracking"),
        ("ByteTrack (Zhang 2022)", "Low-score detection box association"),
        ("YOLOv8 (Jocher 2023)", "Single-stage PAN-FPN anchor-free detector"),
        ("CLAHE (Zuiderveld 1994)", "Luminance adaptive contrast equalization"),
        ("PPE Containment (Fang 2018)", "Two-stage spatial bounding box attribution"),
        ("Hysteresis (Sultani 2018)", "Dual-threshold temporal voting eliminates flicker"),
        ("Edge-Cloud IoT (Satyanarayanan 2017)", "Tiered architecture: capture nodes + edge host"),
        ("Tail at Scale (Dean 2013)", "Async queuing with drop-stale latency mitigation"),
        ("ARIES / WAL (Mohan 1992)", "Write-Ahead Logging for non-blocking DB writes"),
        ("ONNX Runtime (Microsoft 2020)", "Graph optimization for 2-4x faster CPU inference"),
        ("OSNet Re-ID (Zhou 2019)", "Multi-scale feature extraction for person Re-ID")
    ]
    for auth, desc in built_papers:
        p = p1_tf.add_paragraph()
        p.text = f"✔ {auth}: "
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = RGBColor(16, 120, 80)
        r = p.add_run()
        r.text = desc
        r.font.bold = False
        r.font.size = Pt(9.5)
        r.font.color.rgb = TEXT_MUTED

    add_card(s9, 6.8, 1.5, 5.7, 5.4, "Roadmap & Future Scope (4 Papers)", RGBColor(180, 120, 10))
    p2_tb = s9.shapes.add_textbox(Inches(7.0), Inches(2.05), Inches(5.3), Inches(4.7))
    p2_tf = p2_tb.text_frame
    p2_tf.word_wrap = True
    roadmap_papers = [
        ("Struck-By Proximity (Ray & Teizer 2012) · PARTIAL", "2D machinery/vehicle classification active. Roadmap: 3D metric Euclidean distance calculation via calibrated camera homography."),
        ("TinyML on Node (David 2021) · PLANNED", "Ultra-lightweight quantized person-presence filter directly on ESP32 to eliminate streaming empty frames."),
        ("Pose Estimation (Cao 2019 / OpenPose) · PLANNED", "Skeleton keypoint analysis to detect worker falls from height and unsafe ergonomic postures."),
        ("Closed-Loop IoT Actuation (Al-Fuqaha 2015) · PLANNED", "Bi-directional telemetry enabling server to trigger physical sirens/buzzers and LED beacons on the ESP32 node.")
    ]
    for auth, desc in roadmap_papers:
        p = p2_tf.add_paragraph()
        p.text = f"🚀 {auth}\n"
        p.font.bold = True
        p.font.size = Pt(10.5)
        p.font.color.rgb = RGBColor(180, 120, 10)
        r = p.add_run()
        r.text = f"   {desc}\n"
        r.font.bold = False
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════════
    # SLIDE 10: Deployment Options, IoT Expansion & Conclusion (Slides 17-20)
    # ══════════════════════════════════════════════════════════════════════════
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "10", "Deployment & Vision", "Production Deployment, IoT Expansion & Summary")

    # Left: Deployment Options (Slide 19)
    add_card(s10, 0.8, 1.5, 5.6, 5.4, "Production Deployment Pathways", RGBColor(14, 110, 180))
    d_tb = s10.shapes.add_textbox(Inches(1.05), Inches(2.1), Inches(5.1), Inches(4.5))
    d_tf = d_tb.text_frame
    d_tf.word_wrap = True
    deps = [
        ("Local Host (Current MVP)", "ESP32-CAM to local PC (FastAPI + YOLOv8n + SQLite WAL). Zero cloud cost, sub-50 ms latency, no internet needed."),
        ("Edge Gateway (Jetson Orin Nano)", "Deploy TensorRT FP16/INT8 on an onsite fanless edge box handling 8+ IP RTSP streams."),
        ("Hybrid Cloud (AWS ECS + Triton)", "Edge nodes stream to AWS ECS cluster with Triton Inference Server; long-term analytics stored on S3."),
        ("Containerized Docker Suite", "Docker Compose stack (fastapi-core, nginx, redis, postgres) for one-click deployment at site offices.")
    ]
    for t, d in deps:
        p = d_tf.add_paragraph()
        p.text = f"• {t}:\n"
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(14, 110, 180)
        r = p.add_run()
        r.text = f"   {d}\n"
        r.font.bold = False
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_MUTED

    # Right: Summary & Key Achievements (Slide 20)
    add_card(s10, 6.8, 1.5, 5.7, 5.4, "Executive Summary & Achievements", RGBColor(16, 120, 80))
    s_tb = s10.shapes.add_textbox(Inches(7.05), Inches(2.1), Inches(5.2), Inches(4.5))
    s_tf = s_tb.text_frame
    s_tf.word_wrap = True
    achieves = [
        ("Full Edge-to-Host Pipeline", "Operational wireless ESP32-CAM (5 FPS) ingestion to real-time FastAPI inference engine."),
        ("BoT-SORT Deep Re-ID", "Appearance embeddings overcome occlusion ID swapping when workers cross paths."),
        ("Zero Alert Flapping", "Spatial containment (>=50%) and 70/30 temporal hysteresis produce exactly one alert per violation episode."),
        ("A+ Safety Grade (91.25/100)", "Empirically validated with sub-50 ms inference latency and 100% duplicate alert suppression."),
        ("Rigorous Scientific Backing", "Architecture and algorithms benchmarked against 15 seminal computer vision & IoT papers.")
    ]
    for t, d in achieves:
        p = s_tf.add_paragraph()
        p.text = f"★ {t}: "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = RGBColor(16, 120, 80)
        r = p.add_run()
        r.text = f"{d}\n"
        r.font.bold = False
        r.font.size = Pt(10)
        r.font.color.rgb = TEXT_MUTED

    p_qa = s_tf.add_paragraph()
    p_qa.text = "Thank You!  •  Questions & Discussion"
    p_qa.font.size = Pt(14)
    p_qa.font.bold = True
    p_qa.font.color.rgb = ACCENT_DARK
    p_qa.alignment = PP_ALIGN.CENTER

    # Save outputs
    prs.save(str(DEST_PROJECT))
    prs.save(str(DEST_DOWNLOADS))
    print(f"Saved 10-slide deck to:\n- {DEST_PROJECT}\n- {DEST_DOWNLOADS}")

if __name__ == "__main__":
    build_10_slide_deck()
