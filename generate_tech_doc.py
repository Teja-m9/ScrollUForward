"""ScrollUForward - Technical Architecture PDF (ReportLab)"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable

OUT = r"C:\Users\HP\Desktop\ScrollUForward_TechDoc.pdf"

# Colors
BG       = colors.HexColor("#0A0A0A")
ACCENT   = colors.HexColor("#AAFF00")
C_WHITE  = colors.HexColor("#F0F0F0")
C_GREY   = colors.HexColor("#888888")
C_DARK   = colors.HexColor("#111111")
C_MID    = colors.HexColor("#1E1E1E")
C_BLUE   = colors.HexColor("#1976D2")
C_GREEN  = colors.HexColor("#27AE60")
C_TEAL   = colors.HexColor("#1ABC9C")
C_PURPLE = colors.HexColor("#9B59B6")
C_ORANGE = colors.HexColor("#E67E22")
C_RED    = colors.HexColor("#ED4956")


# ── Custom Flowables ──────────────────────────────────────────────────────────
class ColorRect(Flowable):
    def __init__(self, width, height, color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class AccentBar(Flowable):
    """Left accent bar + heading text side by side."""
    def __init__(self, text, font_size=14, color=ACCENT):
        Flowable.__init__(self)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.width = 170 * mm
        self.height = font_size + 8

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.rect(0, 2, 3, self.font_size, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawString(8, 4, self.text)


class InfoBox(Flowable):
    """A shaded box with a title and bullet lines."""
    def __init__(self, title, bullets, border_color=ACCENT, width=170*mm):
        Flowable.__init__(self)
        self.title = title
        self.bullets = bullets
        self.border_color = border_color
        self.box_width = width
        self.height = 16 + len(bullets) * 14

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor("#1A1A1A"))
        c.setStrokeColor(self.border_color)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.box_width, self.height, 6, fill=1, stroke=1)
        c.setFillColor(self.border_color)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10, self.height - 13, self.title)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 9)
        y = self.height - 26
        for line in self.bullets:
            c.setFillColor(C_TEAL)
            c.drawString(14, y, "-")
            c.setFillColor(colors.HexColor("#CCCCCC"))
            c.drawString(22, y, line[:95])
            y -= 13


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    def P(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": P("cover_title", fontName="Helvetica-Bold", fontSize=40,
                          textColor=ACCENT, alignment=TA_CENTER, spaceAfter=6),
        "cover_sub":   P("cover_sub", fontName="Helvetica-Oblique", fontSize=15,
                          textColor=C_GREY, alignment=TA_CENTER, spaceAfter=20),
        "section_num": P("section_num", fontName="Helvetica", fontSize=9,
                          textColor=C_GREY, spaceAfter=2),
        "h1":          P("h1", fontName="Helvetica-Bold", fontSize=24,
                          textColor=ACCENT, spaceAfter=8, spaceBefore=4),
        "h2":          P("h2", fontName="Helvetica-Bold", fontSize=13,
                          textColor=ACCENT, spaceAfter=4, spaceBefore=8),
        "h3":          P("h3", fontName="Helvetica-Bold", fontSize=11,
                          textColor=C_WHITE, spaceAfter=3, spaceBefore=6),
        "body":        P("body", fontName="Helvetica", fontSize=10,
                          textColor=colors.HexColor("#CCCCCC"),
                          spaceAfter=6, leading=15),
        "bullet":      P("bullet", fontName="Helvetica", fontSize=10,
                          textColor=colors.HexColor("#CCCCCC"),
                          spaceAfter=3, leading=14, leftIndent=14,
                          bulletIndent=4, bulletText="-"),
        "code":        P("code", fontName="Courier", fontSize=8,
                          textColor=colors.HexColor("#AAFFAA"),
                          spaceAfter=4, leading=12, backColor=C_DARK),
        "kv_key":      P("kv_key", fontName="Helvetica-Bold", fontSize=10,
                          textColor=ACCENT, spaceAfter=2),
        "kv_val":      P("kv_val", fontName="Helvetica", fontSize=10,
                          textColor=colors.HexColor("#CCCCCC"), spaceAfter=4),
        "footer":      P("footer", fontName="Helvetica", fontSize=8,
                          textColor=C_GREY, alignment=TA_CENTER),
        "caption":     P("caption", fontName="Helvetica-Oblique", fontSize=9,
                          textColor=C_GREY, spaceAfter=6),
        "num":         P("num", fontName="Helvetica", fontSize=10,
                          textColor=colors.HexColor("#CCCCCC"),
                          spaceAfter=3, leading=14, leftIndent=20,
                          bulletIndent=6),
    }


ST = make_styles()


def div():
    return HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#333333"),
                      spaceAfter=8, spaceBefore=4)

def sp(h=6):
    return Spacer(1, h)

def h1(t):  return Paragraph(t, ST["h1"])
def h2(t):  return [AccentBar(t, 13, ACCENT), sp(4)]
def h3(t):  return Paragraph(t, ST["h3"])
def body(t): return Paragraph(t, ST["body"])
def code(t): return Paragraph(t, ST["code"])

def bullets(items, color=None):
    out = []
    for item in items:
        out.append(Paragraph(f"<bullet>-</bullet> {item}", ST["bullet"]))
    return out

def numbered(items):
    out = []
    for i, item in enumerate(items, 1):
        out.append(Paragraph(f"<bullet><b>{i}.</b></bullet> {item}", ST["num"]))
    return out

def kv_table(rows):
    """rows = list of (key, value) tuples."""
    data = []
    for k, v in rows:
        data.append([
            Paragraph(f"<b>{k}</b>", ParagraphStyle("kk", fontName="Helvetica-Bold",
                fontSize=10, textColor=ACCENT)),
            Paragraph(v, ParagraphStyle("vv", fontName="Helvetica", fontSize=10,
                textColor=colors.HexColor("#CCCCCC"), leading=14)),
        ])
    t = Table(data, colWidths=[55*mm, 115*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#111111"), colors.HexColor("#151515")]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return [t, sp(8)]

def two_col_table(rows, widths=(55*mm, 115*mm), header=None, header_colors=(ACCENT, C_WHITE)):
    data = []
    if header:
        data.append([Paragraph(f"<b>{header[0]}</b>", ParagraphStyle("hk", fontName="Helvetica-Bold",
                        fontSize=10, textColor=header_colors[0])),
                     Paragraph(f"<b>{header[1]}</b>", ParagraphStyle("hv", fontName="Helvetica-Bold",
                        fontSize=10, textColor=header_colors[1]))])
    for k, v in rows:
        data.append([
            Paragraph(f"<b>{k}</b>", ParagraphStyle("k2", fontName="Helvetica-Bold",
                fontSize=9, textColor=ACCENT, leading=13)),
            Paragraph(v, ParagraphStyle("v2", fontName="Helvetica", fontSize=9,
                textColor=colors.HexColor("#CCCCCC"), leading=13)),
        ])
    t = Table(data, colWidths=list(widths))
    style = [
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#111111"), colors.HexColor("#161616")]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]
    if header:
        style += [
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1A1A1A")),
            ("LINEBELOW", (0,0), (-1,0), 0.5, ACCENT),
        ]
    t.setStyle(TableStyle(style))
    return [t, sp(8)]


def section_header(num, title):
    return [
        PageBreak(),
        ColorRect(170*mm, 2, ACCENT), sp(8),
        Paragraph(f"SECTION {num}", ST["section_num"]),
        Paragraph(title, ST["h1"]),
        div(),
    ]


# ── Page background setup ─────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Header bar (skip cover page 1)
    if doc.page > 1:
        canvas.setFillColor(colors.HexColor("#111111"))
        canvas.rect(0, A4[1] - 18*mm, A4[0], 18*mm, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, A4[1] - 1.5, A4[0], 1.5, fill=1, stroke=0)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(C_GREY)
        canvas.drawRightString(A4[0] - 18*mm, A4[1] - 12*mm,
                               "ScrollUForward  |  Technical Architecture  |  2026")
        # Footer
        canvas.setFillColor(colors.HexColor("#111111"))
        canvas.rect(0, 0, A4[0], 12*mm, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, 12*mm - 1.5, A4[0], 1.5, fill=1, stroke=0)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(C_GREY)
        canvas.drawCentredString(A4[0]/2, 4*mm, f"Page {doc.page}")
    else:
        # Cover: just accent lines
        canvas.setFillColor(ACCENT)
        canvas.rect(0, A4[1] - 4, A4[0], 4, fill=1, stroke=0)
        canvas.rect(0, 0, A4[0], 4, fill=1, stroke=0)
    canvas.restoreState()


# ── Build content ─────────────────────────────────────────────────────────────
story = []

# ═══ COVER ════════════════════════════════════════════════════════════════════
story += [
    sp(50),
    Paragraph("ScrollUForward", ST["cover_title"]),
    Paragraph("Learn Something Real Every Day", ST["cover_sub"]),
    sp(10),
]

# Cover info table
cover_data = [
    ["Technical Architecture", "& Stack Document"],
    ["Version", "1.0  |  April 2026"],
    ["Project Type", "AI-Powered Educational Mobile App"],
    ["Author", "Teja-m9"],
]
ct = Table(cover_data, colWidths=[60*mm, 110*mm])
ct.setStyle(TableStyle([
    ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 11),
    ("TEXTCOLOR", (0,0), (0,-1), ACCENT),
    ("TEXTCOLOR", (1,0), (1,-1), C_WHITE),
    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1A1A1A")),
    ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#1A1A1A"), colors.HexColor("#111111")]),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("LEFTPADDING", (0,0), (-1,-1), 12),
    ("BOX", (0,0), (-1,-1), 0.8, ACCENT),
    ("LINEBELOW", (0,0), (-1,-2), 0.3, colors.HexColor("#333333")),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
]))
story += [ct, sp(30)]

# Tech stack pills (cover)
stack_data = [
    [Paragraph("<b>Backend</b><br/>FastAPI + Python", ParagraphStyle("sp", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14)),
     Paragraph("<b>Mobile</b><br/>React Native + Expo", ParagraphStyle("sp2", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14)),
     Paragraph("<b>Database</b><br/>Appwrite Cloud", ParagraphStyle("sp3", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14))],
    [Paragraph("<b>Storage</b><br/>AWS S3 (ap-south-1)", ParagraphStyle("sp4", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14)),
     Paragraph("<b>AI Stack</b><br/>Groq / Gemini / Deepgram", ParagraphStyle("sp5", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14)),
     Paragraph("<b>Deployment</b><br/>Railway + Expo Go", ParagraphStyle("sp6", fontName="Helvetica",
        fontSize=10, textColor=C_WHITE, alignment=TA_CENTER, leading=14))],
]
st_t = Table(stack_data, colWidths=[55*mm, 58*mm, 57*mm])
st_t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,0), C_BLUE),
    ("BACKGROUND", (1,0), (1,0), C_GREEN),
    ("BACKGROUND", (2,0), (2,0), C_PURPLE),
    ("BACKGROUND", (0,1), (0,1), C_ORANGE),
    ("BACKGROUND", (1,1), (1,1), C_RED),
    ("BACKGROUND", (2,1), (2,1), C_TEAL),
    ("TOPPADDING", (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ("ROUNDEDCORNERS", [6]),
    ("GRID", (0,0), (-1,-1), 2, BG),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
]))
story += [st_t, PageBreak()]


# ═══ SECTION 1 — Project Overview ════════════════════════════════════════════
story += section_header(1, "Project Overview")
story.append(body(
    "ScrollUForward is a short-form educational content platform built for mobile-first consumption. "
    "It combines TikTok-style vertical reels with rigorous educational content -- every piece of content "
    "(reel, article, news) is AI-generated, quality-scored, bias-checked, and curated before it reaches the user."
))

story += h2("Core Mission")
story.append(body(
    "Deliver bite-sized, accurate, bias-free educational content across 12 knowledge domains "
    "to users who want to learn something real every day -- without the noise of mainstream social media."
))

story += h2("Content Types")
story.append(InfoBox("Three Content Pillars", [
    "Reels -- AI-generated vertical video (Manim animations + TTS narration, 60-120s, 1080x1920)",
    "Articles -- Long-form AI-authored blog posts (800-1200 words) with cover images and citations",
    "News -- Real-time curated news from whitelisted RSS feeds, bias-checked, summarised",
], border_color=C_TEAL))
story.append(sp(8))

story += h2("Knowledge Domains")
domains_data = [["Technology", "AI", "Physics", "Space", "Biology", "History"],
                ["Mathematics", "Philosophy", "Engineering", "Chemistry", "Economics", "Environment"]]
dom_colors_row = [C_BLUE, C_RED, C_PURPLE, C_TEAL, C_GREEN, C_ORANGE]
dt = Table(domains_data, colWidths=[28*mm]*6)
dt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,0), C_BLUE), ("BACKGROUND", (1,0), (1,0), C_RED),
    ("BACKGROUND", (2,0), (2,0), C_PURPLE), ("BACKGROUND", (3,0), (3,0), C_TEAL),
    ("BACKGROUND", (4,0), (4,0), C_GREEN), ("BACKGROUND", (5,0), (5,0), C_ORANGE),
    ("BACKGROUND", (0,1), (0,1), C_ORANGE), ("BACKGROUND", (1,1), (1,1), C_PURPLE),
    ("BACKGROUND", (2,1), (2,1), C_ORANGE), ("BACKGROUND", (3,1), (3,1), C_TEAL),
    ("BACKGROUND", (4,1), (4,1), C_GREEN), ("BACKGROUND", (5,1), (5,1), C_BLUE),
    ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 9),
    ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#0A0A0A")),
    ("ALIGN", (0,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("GRID", (0,0), (-1,-1), 2, BG),
]))
story += [dt, sp(10)]

story += h2("Live Metrics")
story += kv_table([
    ("Reels published",   "12+ (Manim CE + Sora-2 generated)"),
    ("News articles",     "20 trending items refreshed April 2026"),
    ("Blog posts",        "20 long-form articles with S3 cover images"),
    ("IQ gamification",   "watch=+5, read=+10, quiz=+15, discussion=+20, streak=+50"),
    ("Backend URL",       "https://scrolluforward-production.up.railway.app"),
])


# ═══ SECTION 2 — Tech Stack ═══════════════════════════════════════════════════
story += section_header(2, "Full Tech Stack")

story += h2("Mobile App")
story += kv_table([
    ("Framework",       "React Native 0.83.2"),
    ("Build Toolchain", "Expo SDK 55 (Expo Go for dev, EAS Build for production)"),
    ("Navigation",      "@react-navigation/native-stack + bottom-tabs + material-top-tabs"),
    ("HTTP Client",     "Axios 1.x with JWT interceptor via AsyncStorage token injection"),
    ("Video Playback",  "expo-av + expo-video"),
    ("Auth",            "expo-auth-session (Google OAuth implicit flow) + JWT"),
    ("Local Storage",   "@react-native-async-storage (token, saved IDs, preferences)"),
    ("UI Icons",        "@expo/vector-icons (Ionicons 5000+ icons)"),
    ("Animation",       "react-native-reanimated 4.x + react-native-gesture-handler"),
    ("Gradients",       "expo-linear-gradient"),
    ("Image Picker",    "expo-image-picker (avatar uploads)"),
    ("React Version",   "React 19.2.0"),
])

story += h2("Backend API")
story += kv_table([
    ("Framework",       "FastAPI (Python 3.11+) -- async, OpenAPI auto-docs at /docs"),
    ("ASGI Server",     "Uvicorn (production) / uvicorn --reload (development)"),
    ("Auth",            "JWT (python-jose HS256, 72h expiry) + bcrypt password hashing"),
    ("Validation",      "Pydantic v2 models for all request/response schemas"),
    ("DB Client",       "Appwrite Python SDK (appwrite==4.1.0)"),
    ("HTTP Client",     "httpx (async) for Deepgram TTS, Pollinations, external APIs"),
    ("Scheduling",      "APScheduler 3.x -- content pipeline daily cron jobs"),
    ("Moderation",      "OpenAI Moderation API + better-profanity library"),
    ("News Harvest",    "feedparser (10 RSS feeds) + NewsAPI (supplemental)"),
    ("Deployment",      "Railway -- auto-deploy on GitHub push, env secrets managed"),
])

story += h2("Database -- Appwrite Cloud")
story += kv_table([
    ("Endpoint",      "https://cloud.appwrite.io/v1"),
    ("Database ID",   "scrolluforward_db"),
    ("Auth Type",     "Server API Key (backend) + JWT (mobile client)"),
])

story.append(h3("Collections Schema"))
coll_rows = [
    ("Collection",         "Purpose"),
    ("users",              "User profiles, IQ scores, badges, interest tags, follow counts"),
    ("content",            "Unified feed -- reels, articles, news (differentiated by content_type)"),
    ("interactions",       "Likes, saves, views, shares per user per content item"),
    ("discussions",        "AI discussion rooms -- title, domain, participant/comment counts"),
    ("comments",           "Flat comment thread per discussion; AI replies as 'ScrollU AI'"),
    ("content_comments",   "Comments on articles, news items, and reels"),
    ("chat_rooms",         "Direct message room metadata (participants, last_message)"),
    ("messages",           "Individual chat messages (body, sender_id, timestamp, is_read)"),
    ("user_violations",    "Moderation strikes, temp bans, permanent ban records"),
]
story += two_col_table(coll_rows[1:], header=coll_rows[0])

story += h2("Media Storage -- AWS S3")
story += kv_table([
    ("Bucket",          "scrolluforward-media"),
    ("Region",          "ap-south-1 (Mumbai)"),
    ("Access Pattern",  "Pre-signed URLs (7-day expiry) -- private bucket, no public access"),
    ("Reel videos",     "reels/{domain}/{date}/{reel_id}.mp4"),
    ("Thumbnails",      "reels/{domain}/{date}/{id}_thumb.jpg"),
    ("News thumbs",     "news/thumbnails/{date}/{news_id}.jpg"),
    ("CDN (planned)",   "AWS CloudFront -- cdn.scrolluforward.com"),
])


# ═══ SECTION 3 — AI & Content Pipeline ═══════════════════════════════════════
story += section_header(3, "AI & Content Pipeline")

story += h2("AI Models Used")

ai_models = [
    ("Groq LLaMA-3.3-70B",  "Primary reasoning model. Used for: article drafting, blog editing, news scoring, bias detection, discussion AI assistant, quiz generation, content validation, domain classification. Temperature: 0.7-0.8. Fast fallback: llama-3.1-8b-instant."),
    ("Deepgram Aura-2",      "Text-to-speech for reel narration. Model: aura-2-athena-en. REST API (POST /v1/speak). Output: MP3, 128kbps, 60-120s typical duration per reel."),
    ("Manim CE v0.20",       "Python animation engine for all educational reels. Renders 9:16 vertical (540x960, 30fps). Each scene is a Python class. Post-render: FFmpeg upscales to 1080x1920 and syncs with TTS audio."),
    ("OpenAI GPT-4o",        "Content moderation via Moderation API. Scans user submissions for hate speech, violence, harassment. Threshold: 0.7 per category."),
    ("OpenAI Sora-2",        "AI video generation for anime-style reels. API: videos.create(model='sora-2', size='720x1280', seconds=4/8/12). Valid durations: 4, 8, 12 seconds only."),
    ("Google Gemini/Imagen", "Blog cover image generation via google-generativeai SDK (Imagen 3.0). 16:9 ratio, uploaded to S3."),
    ("Pollinations.ai",      "Free Stable Diffusion/Flux image API. No API key. Endpoint: image.pollinations.ai/prompt/{encoded}?model=flux. Rate limit: ~1 req/8s."),
    ("LoremFlickr",          "CC-licensed Flickr photos by keyword. No rate limits, no API key. Used as primary source for news thumbnails. Endpoint: loremflickr.com/800/450/{keywords}."),
]
story += two_col_table(ai_models, widths=(42*mm, 128*mm))

story += h2("Content Generation Pipeline")
story += numbered([
    "Orchestrator triggers daily (APScheduler cron)",
    "Domain Rotation: 5 domains selected per day from 12 total (day-of-year mod 12)",
    "Parallel: Reel Agent (x5 domains) + Blog Agent (x5 domains) + News Agent (all feeds)",
    "Each agent produces structured output: quality_score, domain, content_type",
    "Validation Gate: entertainment filter + quality score (threshold: 65/100) + bias check",
    "Domain Router publishes passing items to Appwrite content collection",
    "Media (MP4, images) uploaded to S3; presigned URLs stored in Appwrite",
    "Mobile feed fetches from /content/feed/personalized/ with domain-based ranking",
])
story.append(sp(8))

story += h2("Reel Generation -- Step by Step")
story += numbered([
    "Write narration script (text per scene)",
    "TTS: Deepgram Aura-2 generates MP3 -- measure exact duration via FFmpeg probe",
    "Manim renders Python scene class at 540x960 @ 30fps to raw MP4",
    "FFmpeg setpts: video duration stretched to match audio (pts = audio_dur / video_dur)",
    "FFmpeg scale: upscale to 1080x1920 with lanczos filter (sharper than bilinear)",
    "Mux: video + audio merged into final MP4 (libx264 fast, CRF 20)",
    "Upload to S3 -- generate presigned URL -- extract thumbnail at 4s mark",
    "Publish to Appwrite content collection with all metadata",
])
story.append(sp(8))

story += h2("News Pipeline -- Step by Step")
story += numbered([
    "Harvest: 10 RSS feeds (Nature, NASA, ArXiv, BBC Science, etc.) + NewsAPI",
    "Score: Groq LLaMA scores each article 0-100 (domain_match, novelty, credibility, readability)",
    "Select: Top 20 articles, balanced across domains (max 2 per domain)",
    "Summarise: Groq generates 3-sentence neutral summary per article",
    "Bias Check: Groq detects political language, propaganda, inflammatory rhetoric -- removes flagged items",
    "Thumbnail: LoremFlickr photo fetched by keyword -- uploaded to S3",
    "Publish: All 20 news items written to Appwrite content collection",
])


# ═══ SECTION 4 — API Architecture ════════════════════════════════════════════
story += section_header(4, "API Architecture")

story.append(body(
    "<b>Production Base URL:</b> https://scrolluforward-production.up.railway.app  |  "
    "Swagger UI: /docs  |  All write endpoints require JWT Bearer token."
))

story += h2("Route Modules")
route_rows = [
    ("Route Prefix",    "Endpoints"),
    ("/auth",           "POST /register, POST /login, POST /google, GET /me"),
    ("/content",        "GET /feed/personalized, CRUD, GET /search, POST /{id}/interact, comments"),
    ("/users",          "GET /{id}, PUT /profile, POST /{id}/follow, POST /iq/earn, GET /leaderboard"),
    ("/discussions",    "CRUD rooms, GET/POST comments, POST /ai/chat, GET /user/{id}/history"),
    ("/chat",           "POST /rooms, GET /rooms, POST /messages, GET /messages/{room_id}"),
    ("/pipeline",       "GET /status, POST /run, GET /run/{id}, POST /agent, GET /domains/today"),
    ("/quiz",           "POST /generate, POST /submit, GET /leaderboard"),
    ("/admin",          "Content moderation dashboard, ban management"),
]
story += two_col_table(route_rows[1:], header=route_rows[0])

story += h2("Auth Flow")
story += numbered([
    "User registers: email+password -- bcrypt hash (cost 12) stored in Appwrite users collection",
    "Login returns JWT: HS256, 72h expiry, payload={sub: user_id, username, email}",
    "Mobile stores JWT in AsyncStorage -- Axios interceptor auto-injects as 'Bearer {token}'",
    "Google OAuth: expo-auth-session implicit flow -- Google ID token -- backend verifies -- issues JWT",
    "Protected endpoints: FastAPI Depends(get_current_user) decodes and validates token on every request",
])

story += h2("Personalized Feed Logic")
story += numbered([
    "User interest_tags stored in profile (set at onboarding, updated via interactions)",
    "GET /content/feed/personalized/ queries content ordered by $createdAt desc",
    "Domain filtering: content matching user's interest_tags surfaced first",
    "Quality score weighting: higher quality_score content prioritised within each domain",
    "Fallback: if no personalization data, returns latest content across all 12 domains",
])


# ═══ SECTION 5 — Discussion Rooms ════════════════════════════════════════════
story += section_header(5, "AI Discussion Rooms")

story.append(body(
    "Discussion rooms are the social learning layer of ScrollUForward. Users debate, ask questions, "
    "and explore ideas in topic-specific rooms with a live AI assistant (ScrollU AI) -- powered by "
    "Groq LLaMA-3.3-70B -- that participates, answers questions, and asks follow-ups."
))

story += h2("Room Types")
story.append(InfoBox("Category Rooms (AI-Powered)", [
    "Created by system -- creator_username = 'ScrollU AI'",
    "AI responds to every single message in the room",
    "Seeded with topic-relevant starter discussions across all 12 domains",
], border_color=ACCENT))
story.append(sp(4))
story.append(InfoBox("Custom Rooms (User-Created)", [
    "Created by any authenticated user with any title and domain",
    "AI responds when: message is a question OR every 3rd message",
    "Other users can join, browse, and participate",
], border_color=C_TEAL))
story.append(sp(8))

story += h2("Chat Persistence (Updated Feature)")
story += numbered([
    "User sends message -- optimistic UI update shown instantly in chat",
    "User message saved to Appwrite comments collection: POST /discussions/{id}/comments",
    "AI chat API called with discussion_id included in request body",
    "Backend generates AI reply via Groq LLaMA-3.3-70B (max 300 tokens, temp 0.8)",
    "Backend auto-saves AI reply to comments (user_id='scrollu_ai', username='ScrollU AI')",
    "AI reply returned to mobile and displayed in real-time",
    "Full conversation retrievable via GET /discussions/user/{user_id}/history",
])

story += h2("Profile Chats Tab")
story.append(body(
    "The user profile now includes a 'Chats' tab showing all discussion rooms they participated in. "
    "Each room displays the full chronological message history -- user messages (green), "
    "AI replies (dark blue) -- with timestamps. Tapping a room opens a full-screen chat viewer."
))

story += h2("Moderation in Discussions")
story += numbered([
    "Every user comment scanned by OpenAI Moderation API before saving",
    "Checks: hate speech, violence, sexual content, self-harm, harassment (threshold: 0.7)",
    "Violation recorded in user_violations collection with type, content snippet, timestamp",
    "Strike 1 -- content rejected + warning. Strike 2 -- 24h ban. Strike 3 -- permanent ban.",
])


# ═══ SECTION 6 — Gamification ════════════════════════════════════════════════
story += section_header(6, "Gamification & IQ System")

story.append(body(
    "Every meaningful interaction earns IQ points, creating a progression system "
    "that rewards deeper educational engagement."
))

story += h2("IQ Point Values")
iq_rows = [
    ("Action",               "Points", "Condition"),
    ("Watch a Reel",         "+5",     "Awarded on reel playback completion"),
    ("Read an Article",      "+10",    "Awarded on full article scroll"),
    ("Complete a Quiz",      "+15",    "Awarded on quiz submission"),
    ("Post in Discussion",   "+20",    "Awarded on first comment per session"),
    ("Daily Streak Bonus",   "+50",    "Awarded for 7-day consecutive engagement"),
    ("Viral Content",        "+100",   "Awarded when user post reaches 1,000 views"),
]
iq_t = Table(iq_rows, colWidths=[65*mm, 25*mm, 80*mm])
iq_t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1A1A1A")),
    ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("FONTSIZE", (0,0), (-1,-1), 10),
    ("TEXTCOLOR", (0,1), (0,-1), colors.HexColor("#CCCCCC")),
    ("TEXTCOLOR", (1,1), (1,-1), C_GREEN),
    ("FONTNAME", (1,1), (1,-1), "Helvetica-Bold"),
    ("TEXTCOLOR", (2,1), (2,-1), C_GREY),
    ("FONTSIZE", (2,1), (2,-1), 9),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#111111"), colors.HexColor("#151515")]),
    ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("LINEBELOW", (0,0), (-1,0), 0.5, ACCENT),
    ("GRID", (0,0), (-1,-1), 0.2, colors.HexColor("#2A2A2A")),
]))
story += [iq_t, sp(10)]

story += h2("Badges (Planned)")
story += bullets([
    "First Reel Watched -- complete first video",
    "Knowledge Seeker -- read 10 articles",
    "Discussion Leader -- post 50 comments",
    "Streak Master -- 30-day consecutive engagement",
    "Domain Expert -- score top 10 in a specific knowledge domain",
])


# ═══ SECTION 7 — Infrastructure ══════════════════════════════════════════════
story += section_header(7, "Infrastructure & Deployment")

story += h2("Production Environment")
story += kv_table([
    ("Backend hosting",  "Railway -- auto-deploy on push to main branch (GitHub integration)"),
    ("Backend URL",      "https://scrolluforward-production.up.railway.app"),
    ("Database",         "Appwrite Cloud -- cloud.appwrite.io (serverless, EU region)"),
    ("Media storage",    "AWS S3 -- ap-south-1 (Mumbai), private bucket + presigned URLs"),
    ("Mobile dev",       "Expo Go + local or Railway backend"),
    ("Mobile prod",      "EAS Build -- APK/IPA (planned; currently Expo Go)"),
    ("CDN (planned)",    "AWS CloudFront -- cdn.scrolluforward.com"),
])

story += h2("Environment Variables")
env_rows = [
    ("Variable Group",         "Variables"),
    ("Appwrite",               "APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY, APPWRITE_DATABASE_ID"),
    ("Auth",                   "JWT_SECRET (HS256 signing key, 72h expiry)"),
    ("Groq AI",                "GROQ_API_KEY (LLaMA-3.3-70B for all reasoning tasks)"),
    ("Google AI",              "GOOGLE_AI_API_KEY (Gemini / Imagen 3.0 cover images)"),
    ("OpenAI",                 "OPENAI_API_KEY (GPT-4o moderation + Sora-2 video)"),
    ("Deepgram TTS",           "DEEPGRAM_API_KEY (Aura-2-athena-en narration)"),
    ("AWS S3",                 "S3_ACCESS_KEY, S3_SECRET_KEY, AWS_S3_BUCKET, S3_REGION"),
    ("Google OAuth",           "GOOGLE_CLIENT_ID_WEB, GOOGLE_CLIENT_SECRET, GOOGLE_CLIENT_ID_ANDROID"),
    ("News",                   "NEWSAPI_KEY (supplemental news source beyond RSS feeds)"),
]
story += two_col_table(env_rows[1:], header=env_rows[0])

story += h2("Local Development Setup")
story.append(h3("Backend"))
story += bullets([
    "Python 3.11+ required",
    "pip install -r requirements.txt",
    "Copy .env.example to .env -- fill all API keys",
    "uvicorn main:app --reload --port 8000",
    "Swagger UI available at http://localhost:8000/docs",
])
story.append(h3("Reel Generation (local only -- not deployed)"))
story += bullets([
    "pip install manim  (Manim CE not on Railway -- runs locally only)",
    "FFmpeg at C:\\KMPlayer\\ffmpeg.exe (path in run_*.py scripts)",
    "Run: python backend/run_f1_reel.py  (or any run_*.py script)",
    "Pipeline: Manim render -> TTS -> FFmpeg sync -> S3 upload -> Appwrite publish",
])
story.append(h3("Mobile"))
story += bullets([
    "Node.js 18+ and npm required",
    "cd mobile && npm install",
    "Update API_BASE_URL in src/api.js to your backend URL",
    "npx expo start -- scan QR with Expo Go app",
])


# ═══ SECTION 8 — Screen Map ═══════════════════════════════════════════════════
story += section_header(8, "Screen & Feature Map")

story += h2("App Screens")
screen_rows = [
    ("Screen",               "Description"),
    ("Splash/Onboarding",    "Interest tag selection, domain personalisation setup"),
    ("Login/Register",       "Email+password auth + Google OAuth implicit flow"),
    ("Home Feed",            "Vertical scroll of reels, articles, news -- TikTok-style"),
    ("Reel Player",          "Full-screen 1080x1920 video with like/save/share overlay"),
    ("Article Reader",       "Full markdown article, cover image, citations, comments"),
    ("News Feed",            "Card grid of 20 trending news items with S3 thumbnails"),
    ("Discussions",          "AI-powered + custom discussion rooms, chat-style UI"),
    ("Chat (DMs)",           "Direct message rooms with persisted message history"),
    ("Profile",              "Posts / Saved / Chats / Badges tabs, IQ score, follow stats"),
    ("Search",               "Full-text content search across all content types"),
    ("Leaderboard",          "Global IQ ranking with top users"),
    ("Quiz",                 "AI-generated quiz per domain, IQ awarded on completion"),
    ("Settings",             "Dark/light theme, notifications, account management"),
]
story += two_col_table(screen_rows[1:], header=screen_rows[0])

story += h2("Navigation Structure")
story.append(InfoBox("Bottom Tab Navigator", [
    "Home (Feed) -- main content stream",
    "Search -- content discovery across all types",
    "Discussions -- AI rooms + direct messages",
    "Profile -- user account and history",
], border_color=C_BLUE))
story.append(sp(4))
story.append(InfoBox("Stack Navigator (within tabs)", [
    "Home -> Reel Player, Article Reader, News Detail",
    "Discussions -> Room Detail (chat view), Create Room",
    "Profile -> Edit Profile, Other User Profile, Followers/Following",
], border_color=C_PURPLE))
story.append(sp(8))


# ═══ SECTION 9 — Security & Moderation ═══════════════════════════════════════
story += section_header(9, "Security & Moderation")

story += h2("Authentication Security")
story += bullets([
    "Passwords hashed with bcrypt (cost factor 12) -- never stored in plaintext",
    "JWTs signed with HS256, 72-hour expiry, validated server-side on every protected request",
    "Google OAuth tokens verified server-side before issuing ScrollUForward JWT",
    "All API keys stored in Railway environment variables -- never committed to source code",
])

story += h2("Three-Strike Moderation System")
story += numbered([
    "User submits text (discussion comment, review) -- passes to OpenAI Moderation API",
    "OpenAI checks: hate, violence, sexual content, self-harm, harassment (threshold: 0.7)",
    "better-profanity library provides secondary explicit language filter",
    "Violation: content rejected, record written to user_violations collection",
    "Strike 1 -- content rejected + warning message returned to user",
    "Strike 2 -- 24-hour temporary ban (403 on all write operations)",
    "Strike 3 -- permanent account ban",
])

story += h2("AI Content Quality Gate")
story += numbered([
    "All AI-generated content runs through validation.py before publishing",
    "Entertainment filter: Groq classifies educational vs entertainment -- entertainment rejected",
    "Quality scorer: factual accuracy (0-30) + readability (0-30) + structure (0-20) + originality (0-20)",
    "Minimum quality score: 65/100 -- below threshold, content is discarded",
    "Bias checker for news: political language, propaganda detected and removed",
    "Duplicate detection: cosine similarity threshold 0.92 -- near-identical content rejected",
])


# ═══ SECTION 10 — File Structure ═════════════════════════════════════════════
story += section_header(10, "Project File Structure")

story += h2("Backend")
be_files = [
    ("main.py",                    "FastAPI app entry, router registration, CORS"),
    ("config.py",                  "All env vars, collection IDs, model names, thresholds"),
    ("auth.py",                    "JWT encode/decode, get_current_user dependency"),
    ("appwrite_client.py",         "Appwrite client factory (databases, users, storage)"),
    ("s3_client.py",               "S3 upload functions, presigned URL generation"),
    ("moderation.py",              "OpenAI moderation API + profanity filter wrapper"),
    ("strike_system.py",           "Violation recording + ban status check"),
    ("schemas.py",                 "Pydantic v2 request/response models"),
    ("routes/auth_routes.py",      "/auth -- register, login, google OAuth, /me"),
    ("routes/content_routes.py",   "/content -- feed, CRUD, search, interact, comments"),
    ("routes/discussion_routes.py","/discussions -- rooms, comments, AI chat, user history"),
    ("routes/chat_routes.py",      "/chat -- room creation and message management"),
    ("routes/user_routes.py",      "/users -- profile, follow, IQ earn, leaderboard"),
    ("routes/pipeline_routes.py",  "/pipeline -- agent triggers and status"),
    ("routes/quiz_routes.py",      "/quiz -- AI quiz generation and scoring"),
    ("agents/orchestrator.py",     "Master pipeline coordinator (parallel agent execution)"),
    ("agents/reel_agent.py",       "Manim reel generation + Deepgram TTS + S3 upload"),
    ("agents/blog_agent.py",       "Article drafting, editing pass, Gemini cover image"),
    ("agents/news_agent.py",       "RSS harvest, score, summarise, bias check pipeline"),
    ("agents/domain_router.py",    "Publish to Appwrite by content_type"),
    ("agents/sora_reel_agent.py",  "OpenAI Sora-2 video generation pipeline"),
    ("agents/validation.py",       "Quality gate, entertainment filter, bias check"),
    ("scenes/f1_reel.py",          "Manim scene: F1 racing legends"),
    ("scenes/amazon_forest_reel.py","Manim scene: Amazon forest importance"),
    ("scenes/israel_iran_reel.py", "Manim + Pollinations: Israel-Iran conflict"),
    ("scenes/kurzgesagt_blackhole_reel.py", "Manim scene: Black hole physics"),
]
story += two_col_table(be_files, widths=(68*mm, 102*mm))

story += h2("Mobile")
mob_files = [
    ("App.js",                    "Root: NavigationContainer, AuthContext, ThemeContext"),
    ("src/api.js",                "Axios client + all API method groups (auth, content, discussions, chat...)"),
    ("screens/HomeScreen.js",     "Vertical feed (reels, articles, news) with infinite scroll"),
    ("screens/ReelScreen.js",     "Full-screen vertical video player with controls"),
    ("screens/ArticleScreen.js",  "Long-form article reader with markdown rendering"),
    ("screens/DiscussionsScreen.js","AI discussion rooms + chat UI + message persistence"),
    ("screens/ChatScreen.js",     "Direct message threads with Appwrite-backed storage"),
    ("screens/ProfileScreen.js",  "Tabs: Posts / Saved / Chats / Badges + discussion history"),
    ("screens/SearchScreen.js",   "Full-text search across all content"),
    ("screens/LeaderboardScreen.js","Global IQ rankings"),
    ("screens/QuizScreen.js",     "AI-generated quiz interface"),
    ("screens/LoginScreen.js",    "Email auth + Google OAuth"),
    ("screens/OnboardingScreen.js","Interest tag selection at first launch"),
]
story += two_col_table(mob_files, widths=(68*mm, 102*mm))


# ═══ SECTION 11 — Roadmap ════════════════════════════════════════════════════
story += section_header(11, "Roadmap")

story += h2("Short Term (Next 30 Days)")
story += bullets([
    "EAS Build -- generate production APK/IPA for app store submission",
    "Push notifications -- new content alerts, streak reminders, discussion replies",
    "AWS CloudFront CDN -- eliminate S3 presigned URL expiry issues for media",
    "Badge system -- award badges based on IQ milestones and interaction streaks",
    "Weekly quiz leaderboard -- per-domain rankings reset each week",
])

story += h2("Medium Term (60-90 Days)")
story += bullets([
    "Offline mode -- cache last 10 reels and 5 articles for reading without internet",
    "User-generated content -- allow users to submit articles (AI quality gate still applies)",
    "Real-time discussion -- WebSocket-based live updates in discussion rooms",
    "Multi-language support -- content generation in Hindi, Spanish, French",
    "Domain Expert profiles -- verified specialists can create curated content",
])

story += h2("Long Term (6+ Months)")
story += bullets([
    "Learning paths -- structured sequences of reels + articles + quizzes per topic",
    "Digital certificates -- for completed learning paths and domain mastery",
    "AI Tutor -- personalised 1:1 AI tutoring sessions within the app",
    "B2B / Education partnerships -- white-label for schools and universities",
    "Monetisation -- premium subscription: advanced AI features and ad-free experience",
])


# ── Output ────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT,
    pagesize=A4,
    leftMargin=18*mm,
    rightMargin=18*mm,
    topMargin=22*mm,
    bottomMargin=16*mm,
    title="ScrollUForward Technical Architecture",
    author="Teja-m9",
    subject="Tech Stack & Workflow Documentation",
)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF generated: {OUT}")
import os
size_kb = os.path.getsize(OUT) // 1024
print(f"Size: {size_kb} KB")
