"""Generate a modern, premium widescreen presentation for SiteGuard Capstone Project.
Uses python-pptx with 16:9 widescreen, custom card layouts, and polished typography.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_PATH = Path("d:/projects/MDM capstone/SiteGuard_Capstone_Presentation.pptx")

# ── Color Palette ─────────────────────────────────────────────────────────────
BG_COLOR       = RGBColor(15, 23, 42)     # #0F172A (Deep Slate Navy)
CARD_BG        = RGBColor(30, 41, 59)     # #1E293B (Card Slate)
CARD_BORDER    = RGBColor(51, 65, 85)     # #334155 (Subtle Border)
ACCENT_AMBER   = RGBColor(245, 158, 11)   # #F59E0B (Safety Amber)
ACCENT_CYAN    = RGBColor(14, 165, 233)   # #0EA5E9 (Tech Sky/Cyan)
TEXT_WHITE     = RGBColor(248, 250, 252)  # #F8FAFC (Pure White)
TEXT_MUTED     = RGBColor(148, 163, 184)  # #94A3B8 (Muted Slate)
ACCENT_GREEN   = RGBColor(16, 185, 129)   # #10B981 (Success Emerald)
ACCENT_RED     = RGBColor(239, 68, 68)    # #EF4444 (Alert Crimson)


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_header(slide, category: str, title: str):
        # Category Badge
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf = cat_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = category.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_AMBER
        
        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.6))
        tf2 = title_box.text_frame
        tf2.word_wrap = True
        tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
        p2 = tf2.paragraphs[0]
        p2.text = title
        p2.font.size = Pt(22)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_WHITE

    def add_card(slide, left, top, width, height, title: str = "", accent_color=ACCENT_CYAN):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.5)

        if title:
            # Card Title inside
            tb = slide.shapes.add_textbox(Inches(left + 0.25), Inches(top + 0.2), Inches(width - 0.5), Inches(0.45))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(15)
            p.font.bold = True
            p.font.color.rgb = accent_color

        return card

    # ── SLIDE 1: Title Slide ──────────────────────────────────────────────────
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(2.0), Inches(0.15), Inches(3.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_AMBER
    bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.4), Inches(1.8), Inches(10.5), Inches(3.6))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "SITEGUARD"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p2 = tf.add_paragraph()
    p2.text = "AI-Based Construction Site Worker Safety Monitoring System"
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_AMBER

    p3 = tf.add_paragraph()
    p3.text = "Edge-IoT Ingestion • YOLOv8n Detection • BoT-SORT Deep Re-ID • Temporal Hysteresis Rule Engine"
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_MUTED

    p4 = tf.add_paragraph()
    p4.text = "\nCapstone Project Technical Presentation • Local Host / Edge Architecture"
    p4.font.size = Pt(12)
    p4.font.color.rgb = ACCENT_CYAN

    # ── SLIDE 2: Problem Statement & Objectives ───────────────────────────────
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Context & Challenges", "Construction Safety Problem & Core Objectives")

    add_card(s2, 0.8, 1.6, 5.6, 5.2, "Industry Safety Hazards", ACCENT_AMBER)
    tb = s2.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    points = [
        ("Fatalities & High Non-Compliance", "Construction accounts for 20%+ of workplace fatalities; failure to equip hardhats and vests is the #1 citation."),
        ("Manual Monitoring Bottlenecks", "Safety officers cannot monitor multiple video feeds continuously; fatigue causes missed non-compliances."),
        ("False Alarm Fatigue", "Raw single-frame CV detectors trigger rapid false alarms on momentary occlusions and sensor noise."),
        ("Equipment Hazard Proximity", "Ground workers traversing blind spots near heavy excavators and trucks without active spatial tracking.")
    ]
    for title, desc in points:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    add_card(s2, 6.8, 1.6, 5.7, 5.2, "SiteGuard System Objectives", ACCENT_CYAN)
    tb2 = s2.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    objectives = [
        ("Autonomous Edge Ingestion", "Stream low-latency QVGA/VGA frames from wireless ESP32-CAM nodes over Wi-Fi at 5 FPS."),
        ("Accurate PPE Attribution", "Simultaneous detection of workers and safety gear with strict bounding-box spatial containment (IoU >= 0.50)."),
        ("Identity Preservation via Re-ID", "Track workers across prolonged occlusions using BoT-SORT appearance embeddings and Kalman filtering."),
        ("Temporal Verification (Zero Flapping)", "Require 70% missing PPE persistence over a 10s sliding window before raising an incident."),
        ("Real-Time Dashboard & Telemetry", "Instant WebSocket broadcast, evidence snapshot recording, and SQLite WAL database logging.")
    ]
    for title, desc in objectives:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"✔ {title}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_GREEN
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 3: End-to-End System Pipeline ───────────────────────────────────
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Architecture Overview", "End-to-End System Dataflow & Modular Services")

    steps = [
        ("1. Ingestion", "ESP32-CAM / Webcams stream raw JPEG over HTTP POST at 5 FPS", ACCENT_AMBER),
        ("2. Preprocessing", "CIE LAB color space conversion + Luminance CLAHE enhancement", ACCENT_CYAN),
        ("3. Vision Model", "YOLOv8n (640x640) inference detects Person, PPE & Machinery", ACCENT_CYAN),
        ("4. Re-ID Tracker", "BoT-SORT preserves worker track IDs across visual occlusions", ACCENT_GREEN),
        ("5. Spatial Match", "Containment algorithm assigns PPE boxes to enclosing worker body", ACCENT_GREEN),
        ("6. Safety Engine", "10s sliding window (70% confirm / 30% clear) suppresses noise", ACCENT_AMBER),
        ("7. Persistence", "Evidence JPEG stored; SQLite WAL records incident episode", ACCENT_CYAN),
        ("8. WebSocket UI", "Broadcasts live worker compliance matrix & alerts to Dashboard", ACCENT_AMBER),
    ]

    for idx, (stitle, sdesc, col) in enumerate(steps):
        row = idx // 4
        col_idx = idx % 4
        l = 0.8 + col_idx * 2.95
        t = 1.6 + row * 2.6
        add_card(s3, l, t, 2.75, 2.3, stitle, col)
        tb = s3.shapes.add_textbox(Inches(l + 0.2), Inches(t + 0.7), Inches(2.35), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = sdesc
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_MUTED

    # ── SLIDE 4: Hardware Architecture & IoT Interconnect ────────────────────
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Hardware & Edge Connectivity", "ESP32-CAM IoT Node & Pinout Configuration")

    add_card(s4, 0.8, 1.6, 5.6, 5.2, "ESP32-CAM Specifications & Firmware", ACCENT_AMBER)
    tb = s4.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    h_points = [
        ("SoC Processor", "AI-Thinker ESP32-CAM, Xtensa Dual-Core 32-bit LX6 @ 240 MHz."),
        ("Camera Sensor", "Omnivision OV2640 2MP CMOS; QVGA/VGA streaming @ 5 FPS."),
        ("Memory Subsystem", "520 KB internal SRAM + 4 MB external PSRAM for double buffering."),
        ("Buffer Management", "config.fb_count = 2 in PSRAM with CAMERA_GRAB_LATEST mode."),
        ("HTTP Client Optimization", "Persistent TCP connection with http.setReuse(true) keep-alive."),
        ("Heartbeat Telemetry", "Periodic transmission of Wi-Fi RSSI, camera ID, and free heap.")
    ]
    for title, desc in h_points:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    add_card(s4, 6.8, 1.6, 5.7, 5.2, "AI-Thinker GPIO Hardware Interconnect", ACCENT_CYAN)
    tb2 = s4.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    pins = [
        ("Power & Reset", "PWDN -> GPIO 32  |  RESET -> -1 (Unused)  |  5V DC stabilized VCC"),
        ("Clock Signals", "XCLK -> GPIO 0 (20 MHz)  |  PCLK -> GPIO 22"),
        ("Sync Signals", "VSYNC -> GPIO 25  |  HREF -> GPIO 23"),
        ("SCCB I2C Interface", "SIOD (SDA) -> GPIO 26  |  SIOC (SCL) -> GPIO 27"),
        ("8-Bit Parallel Bus", "Y2: GPIO 5, Y3: GPIO 18, Y4: GPIO 19, Y5: GPIO 21\nY6: GPIO 36, Y7: GPIO 39, Y8: GPIO 34, Y9: GPIO 35"),
        ("Wireless RF", "802.11 b/g/n 2.4 GHz link connecting to FastAPI PC Host Server")
    ]
    for title, desc in pins:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"⚡ {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_AMBER
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 5: Image Processing & Lighting Enhancement ─────────────────────
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Computer Vision Pipeline", "Image Preprocessing & CLAHE Luminance Normalization")

    add_card(s5, 0.8, 1.6, 3.7, 5.2, "1. Color Space Shift", ACCENT_CYAN)
    tb = s5.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "CIE LAB Transformation\n\n• Frame decoded into BGR array.\n• Converted to CIE LAB via cv2.COLOR_BGR2LAB.\n• Separates Luminance (L-channel) from Chrominance (A & B channels).\n• Preserves worker PPE color fidelity (safety orange/neon yellow) without tint distortion."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    add_card(s5, 4.8, 1.6, 3.7, 5.2, "2. CLAHE Equalization", ACCENT_AMBER)
    tb = s5.shapes.add_textbox(Inches(5.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Adaptive Contrast Boosting\n\n• Applied strictly to L-channel.\n• Clip Limit = 2.0 to prevent noise overamplification.\n• Tile Grid Size = (8, 8) for localized enhancement.\n• Recovers hidden workers and PPE under harsh shadows, scaffolding backlighting, and dawn/dusk lighting."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    add_card(s5, 8.8, 1.6, 3.7, 5.2, "3. Letterbox & Normalization", ACCENT_GREEN)
    tb = s5.shapes.add_textbox(Inches(9.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Model Preparation\n\n• Converted back to BGR space.\n• Optional 3x3 Gaussian smoothing to soften JPEG compression noise.\n• Padded aspect-ratio letterboxing to 640x640.\n• Execution benchmark: <4.2 ms on Ryzen 5 CPU, ensuring zero ingestion bottlenecks."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # ── SLIDE 6: Computer Vision Model & Specifications ──────────────────────
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Detection Architecture", "YOLOv8n Specifications & Confidence Gates")

    add_card(s6, 0.8, 1.6, 5.6, 5.2, "Model Architecture & Weights", ACCENT_CYAN)
    tb = s6.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    specs = [
        ("Architecture", "Ultralytics YOLOv8n (Nano) Single-Stage Anchor-Free Detector."),
        ("Model Weight File", "yolov8n_v1_best.pt (~6.2 MB) / ONNX Runtime FP32."),
        ("Inference Resolution", "640 × 640 pixels (optimal resolution/compute tradeoff)."),
        ("Feature Extractor", "Cross-Stage Partial DarkNet with Path Aggregation Network (PAN)."),
        ("NMS IoU Threshold", "Tighter 0.40 threshold (Ultralytics default: 0.70) suppressing duplicate person/vest bounding boxes."),
        ("Dual Runtime Support", "Native PyTorch or ONNX Runtime (2–4× throughput gain on CPU).")
    ]
    for title, desc in specs:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    add_card(s6, 6.8, 1.6, 5.7, 5.2, "Class Taxonomy & Asymmetric Gates", ACCENT_AMBER)
    tb2 = s6.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    classes = [
        ("Person (Gate: 0.35)", "Low threshold ensures workers are never missed even under distant or partially occluded views."),
        ("NO-Hardhat, NO-Vest, NO-Mask (Gate: 0.50)", "High threshold suppresses false positive violation alerts."),
        ("Hardhat, Safety Vest, Mask (Gate: 0.40)", "Balanced threshold detecting equipped safety gear reliably."),
        ("machinery & vehicle (Gate: 0.45)", "Localizes excavators, cranes, trucks, and forklifts on site."),
        ("Safety Cone (Gate: 0.40)", "Identifies restricted physical boundary delineations.")
    ]
    for title, desc in classes:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"🎯 {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_AMBER
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 7: Deep Re-ID & Multi-Object Tracking ──────────────────────────
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Multi-Object Tracking", "BoT-SORT Tracker with Deep Appearance Re-ID")

    add_card(s7, 0.8, 1.6, 5.6, 5.2, "Why Deep Re-ID is Crucial", ACCENT_AMBER)
    tb = s7.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    reid_why = [
        ("The Kalman Filter Limit", "Pure motion trackers (ByteTrack / SORT) lose tracks if workers stop moving or cross paths closely."),
        ("Visual Occlusions", "Workers passing behind pillars or machinery undergo ID switching without visual feature memory."),
        ("Deep Visual Embeddings", "Extracts appearance feature vectors capturing clothing, gear color, and aspect ratios."),
        ("Cosine Similarity Association", "Re-identifies returning workers by matching appearance memory even after 45+ frames of total occlusion.")
    ]
    for title, desc in reid_why:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    add_card(s7, 6.8, 1.6, 5.7, 5.2, "BoT-SORT Implementation (botsort_reid.yaml)", ACCENT_CYAN)
    tb2 = s7.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    params = [
        ("with_reid: True", "Enables deep appearance feature extraction per detected worker bounding box."),
        ("gmc_method: sparseOptFlow", "Global Motion Compensation computes background optical flow to cancel out camera shaking/vibration."),
        ("appearance_thresh: 0.75", "High cosine similarity threshold preventing false identity swaps between workers in similar vests."),
        ("track_buffer: 45 frames", "Maintains lost worker states alive for >9 seconds at 5 FPS to reconnect re-emerging workers."),
        ("fuse_score: True", "Fuses detection confidence score with visual Re-ID cost matrix.")
    ]
    for title, desc in params:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"⚙ {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_GREEN
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 8: Spatial Containment Association ──────────────────────────────
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "PPE-Worker Association", "Geometric Bounding Box Containment Algorithm")

    add_card(s8, 0.8, 1.6, 5.6, 5.2, "Association Formulation", ACCENT_CYAN)
    tb = s8.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Mathematical Definition:\n\n"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_WHITE
    p2 = tf.add_paragraph()
    p2.text = "Containment(B_PPE, B_Person) = Area(B_PPE ∩ B_Person) / Area(B_PPE)\n\n"
    p2.font.bold = True
    p2.font.size = Pt(13)
    p2.font.color.rgb = ACCENT_AMBER
    p3 = tf.add_paragraph()
    p3.text = "• Bounding box containment requires at least 50% (PPE_CONTAINMENT_MIN = 0.50) of the PPE box to lie inside the worker box.\n• Solves the multi-worker attribution problem when two workers stand side-by-side.\n• Loose PPE detections on floors or scaffolding belonging to no worker are discarded."
    p3.font.size = Pt(12)
    p3.font.color.rgb = TEXT_MUTED

    add_card(s8, 6.8, 1.6, 5.7, 5.2, "Conflict Resolution & Per-Worker State", ACCENT_GREEN)
    tb2 = s8.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    c_points = [
        ("Max-Confidence Arbitration", "If a worker has both 'Hardhat' and 'NO-Hardhat' boxes associated, the detection with the higher confidence score wins."),
        ("Worker Checklist Generation", "Produces an atomic per-worker PPE status dictionary: {'helmet': ('ok', 0.82), 'safety_vest': ('missing', 0.74)}."),
        ("Track ID Coupling", "All PPE states are bound to the worker's unique track_id, enabling historical temporal evaluation across frames.")
    ]
    for title, desc in c_points:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"✔ {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_GREEN
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 9: Temporal Hysteresis & Safety Rule Engine ─────────────────────
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Safety Rule Engine", "Dual-Threshold Temporal Hysteresis & Alert Cooldown")

    add_card(s9, 0.8, 1.6, 3.7, 5.2, "10-Second Sliding Window", ACCENT_AMBER)
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Sliding Window Buffer\n\n• Maintains deque of observations per tracked worker.\n• Window duration: 10.0 seconds.\n• Minimum observations required: 3 frames before making any compliance verdict.\n• Worker records auto-expire after 10.0 seconds of absence from the scene."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    add_card(s9, 4.8, 1.6, 3.7, 5.2, "Dual Confirmation Ratios", ACCENT_CYAN)
    tb = s9.shapes.add_textbox(Inches(5.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Hysteresis Gap\n\n• Confirmation Ratio: 70% (item confirmed missing only if absent in >=70% of frames over window).\n• Clearance Ratio: 30% (violation cleared only when missing frames drop <=30%).\n• The 40% gap completely eliminates alert flapping caused by momentary head turns or occlusion."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    add_card(s9, 8.8, 1.6, 3.7, 5.2, "Single-Episode Incidents", ACCENT_GREEN)
    tb = s9.shapes.add_textbox(Inches(9.0), Inches(2.25), Inches(3.3), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Episode-Based Alerts\n\n• Exactly 1 incident created when violation begins.\n• If more items go missing (e.g. vest after helmet), existing incident updates.\n• Zero duplicate alerts during a continuous violation.\n• New alert generated only if worker clears and violates again later."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED

    # ── SLIDE 10: Evaluation & Safety Scorecard ───────────────────────────────
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Evaluation & Validity", "Safety Reliability Scorecard & Performance Metrics")

    add_card(s10, 0.8, 1.6, 5.6, 5.2, "Composite Score Formulation", ACCENT_AMBER)
    tb = s10.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Weighted Scorecard Formula:\n"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = TEXT_WHITE
    p2 = tf.add_paragraph()
    p2.text = "Score = (S_det × 0.35) + (S_lat × 0.25) + (S_up × 0.20) + (S_dup × 0.20)\n\n"
    p2.font.bold = True
    p2.font.size = Pt(13)
    p2.font.color.rgb = ACCENT_AMBER
    p3 = tf.add_paragraph()
    p3.text = "• S_det (35%): Detection precision & recall on worker PPE.\n• S_lat (25%): Inference responsiveness (<100 ms on CPU).\n• S_up (20%): System uptime & camera heartbeat stability.\n• S_dup (20%): Duplicate suppression via episode tracking."
    p3.font.size = Pt(12)
    p3.font.color.rgb = TEXT_MUTED

    add_card(s10, 6.8, 1.6, 5.7, 5.2, "Operational Scorecard Results", ACCENT_GREEN)
    tb2 = s10.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    res = [
        ("Overall Score", "91.2 / 100 — Grade A+", ACCENT_GREEN),
        ("Detection Reliability", "85.0 / 100", TEXT_WHITE),
        ("Latency Performance", "90.0 / 100 (Avg inference: 48.2 ms)", TEXT_WHITE),
        ("System Uptime", "95.0 / 100 (Zero crash daemon loop)", TEXT_WHITE),
        ("Duplicate Suppression", "100.0 / 100 (Zero duplicate incident rows)", ACCENT_GREEN),
        ("Total Incidents Logged", "158 validated safety violations", TEXT_MUTED)
    ]
    for title, val, col in res:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"★ {title}: "
        p.font.bold = True
        p.font.size = Pt(13)
        p.font.color.rgb = col
        run = p.add_run()
        run.text = f"{val}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_WHITE

    # ── SLIDE 11: 15 Research Papers Benchmark Matrix ─────────────────────────
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Literature Justification", "Benchmark Matrix: 15 Research Papers & Implementation Status")

    # Table of papers
    rows = 9
    cols = 4
    table_shape = s11.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.3))
    table = table_shape.table
    table.columns[0].width = Inches(2.3)
    table.columns[1].width = Inches(2.5)
    table.columns[2].width = Inches(5.1)
    table.columns[3].width = Inches(1.8)

    headers = ["Paper / Author", "Topic / Method", "Scientific Justification", "Status"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = ACCENT_AMBER

    paper_rows = [
        ("BoT-SORT (Aharon 2022)", "Re-ID + GMC Tracking", "Deep appearance vectors prevent ID swaps across occlusions", "IMPLEMENTED"),
        ("ByteTrack (Zhang 2022)", "Low-Score Box Tracking", "Associates weak detection boxes to bridge occlusion gaps", "IMPLEMENTED"),
        ("YOLOv8 (Jocher 2023)", "Anchor-Free Detection", "PAN-FPN architecture enables 50ms real-time CPU inference", "IMPLEMENTED"),
        ("CLAHE (Zuiderveld 1994)", "Luminance Contrast", "Boosts dark/backlit outdoor frames without color distortion", "IMPLEMENTED"),
        ("Hierarchical PPE (Fang 2018)", "Spatial Containment", "Two-stage containment attributes PPE strictly to worker body", "IMPLEMENTED"),
        ("Hysteresis Anomaly (Sultani 2018)", "Dual-Threshold Window", "Eliminates single-frame detection flickering and false alerts", "IMPLEMENTED"),
        ("Edge-Cloud IoT (Satyanarayanan 2017)", "Tiered Architecture", "Partitions capture nodes (ESP32) and local edge server", "IMPLEMENTED"),
        ("Machinery Zones (Ray & Teizer 2012)", "Struck-By Proximity", "2D machinery detection active; 3D metric Euclidean distance", "ROADMAP / PARTIAL"),
    ]

    for r_idx, r_data in enumerate(paper_rows, start=1):
        for c_idx, val in enumerate(r_data):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG if r_idx % 2 == 0 else RGBColor(20, 30, 48)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                if c_idx == 3:
                    p.font.bold = True
                    p.font.color.rgb = ACCENT_GREEN if "IMPLEMENTED" in val else ACCENT_AMBER
                else:
                    p.font.color.rgb = TEXT_WHITE if c_idx == 0 else TEXT_MUTED

    # ── SLIDE 12: Deployment Strategies & Future Roadmap ──────────────────────
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Deployment & Roadmap", "Production Deployment Options & Future Enhancements")

    add_card(s12, 0.8, 1.6, 5.6, 5.2, "Deployment Options", ACCENT_CYAN)
    tb = s12.shapes.add_textbox(Inches(1.05), Inches(2.25), Inches(5.1), Inches(4.3))
    tf = tb.text_frame
    tf.word_wrap = True
    deps = [
        ("Option 1: Local Host (Current)", "PC Server (Ryzen 5 CPU) running FastAPI + YOLO + SQLite WAL. Zero cloud cost, sub-50ms latency."),
        ("Option 2: Edge Gateway (Jetson Orin Nano)", "Migrate to FP16/INT8 TensorRT on an onsite fanless edge box handling 8+ IP RTSP streams."),
        ("Option 3: Hybrid Cloud (AWS ECS / Triton)", "Centralized multi-site oversight across nationwide construction projects with cold-storage analytics on S3."),
        ("Option 4: Containerized On-Premise Suite", "Docker Compose bundle (fastapi-core, nginx, redis, postgres) for plug-and-play onsite setup.")
    ]
    for title, desc in deps:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p.text = f"• {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    add_card(s12, 6.8, 1.6, 5.7, 5.2, "Roadmap & Future Capabilities", ACCENT_AMBER)
    tb2 = s12.shapes.add_textbox(Inches(7.05), Inches(2.25), Inches(5.2), Inches(4.3))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    roadmap = [
        ("3D Metric Proximity Zones", "Calculate Euclidean ground distances using calibrated pinhole camera homography rather than 2D bounding boxes."),
        ("On-Node TinyML Filtering", "Deploy a quantized person-presence wake-up detector directly on ESP32 before network transmission."),
        ("Skeleton Pose Estimation", "Integrate YOLOv8-pose to classify slips, trips, falls from height, and ergonomic risk factors."),
        ("Bi-Directional IoT Actuation", "Reverse HTTP/MQTT commands triggering sirens and strobe LEDs on ESP32 GPIO 4 during critical violations.")
    ]
    for title, desc in roadmap:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"🚀 {title}:\n"
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = ACCENT_AMBER
        run = p.add_run()
        run.text = f"   {desc}\n"
        run.font.bold = False
        run.font.color.rgb = TEXT_MUTED

    # ── SLIDE 13: Summary & Q&A Slide ─────────────────────────────────────────
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)

    add_card(s13, 2.0, 1.5, 9.333, 4.5, "", ACCENT_AMBER)
    tb = s13.shapes.add_textbox(Inches(2.5), Inches(2.0), Inches(8.333), Inches(3.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "SiteGuard: Summary of Achievements"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.alignment = PP_ALIGN.CENTER

    achievements = [
        "End-to-End Edge-to-Host Pipeline with ESP32-CAM (5 FPS) and FastAPI Backend",
        "YOLOv8n + BoT-SORT Deep Appearance Re-ID resolving visual occlusion ID swaps",
        "Spatial Containment (IoU >= 0.50) with Dual-Threshold Temporal Hysteresis (70%/30%)",
        "Validated 91.2/100 Safety Score (Grade A+) with Zero Duplicate Incident Flapping",
        "Rigorous Benchmark of 15 Research Papers Supporting All Architectural Choices"
    ]
    for ach in achievements:
        p = tf.add_paragraph()
        p.text = f"✓  {ach}"
        p.font.size = Pt(13)
        p.font.color.rgb = ACCENT_CYAN
        p.alignment = PP_ALIGN.CENTER

    p_qa = tf.add_paragraph()
    p_qa.text = "\nThank You!  •  Questions & Discussion"
    p_qa.font.size = Pt(18)
    p_qa.font.bold = True
    p_qa.font.color.rgb = ACCENT_AMBER
    p_qa.alignment = PP_ALIGN.CENTER

    prs.save(str(OUTPUT_PATH))
    print(f"Presentation successfully saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    create_deck()
