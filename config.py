"""config.py — app-wide constants, stage definitions, column map."""
import os

# ── Sheet names ────────────────────────────────────────────────────
SHEET_PAPERS   = "Papers"
SHEET_ACTIVITY = "Activity"
SHEET_JOURNALS = "Journals"

# ── OAuth ──────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# ── Pipeline stages ────────────────────────────────────────────────
STAGES = [
    {"id": "idea",           "label": "Idea",           "icon": "💡"},
    {"id": "literature",     "label": "Literature",     "icon": "📚"},
    {"id": "methodology",    "label": "Methodology",    "icon": "🔬"},
    {"id": "datacollection", "label": "Data Collection","icon": "📊"},
    {"id": "analysis",       "label": "Analysis",       "icon": "📈"},
    {"id": "writing",        "label": "Writing",        "icon": "✍️"},
    {"id": "submitted",      "label": "Submitted",      "icon": "📤"},
    {"id": "peerreview",     "label": "Peer Review",    "icon": "👁"},
    {"id": "revision",       "label": "Revision",       "icon": "🔄"},
    {"id": "accepted",       "label": "Accepted",       "icon": "✅"},
    {"id": "published",      "label": "Published",      "icon": "🏆"},
]
STAGE_IDS    = [s["id"]    for s in STAGES]
STAGE_LABELS = {s["id"]: s["label"] for s in STAGES}
STAGE_ICONS  = {s["id"]: s["icon"]  for s in STAGES}

STAGE_PROGRESS = {
    "idea": 5, "literature": 15, "methodology": 25,
    "datacollection": 40, "analysis": 55, "writing": 70,
    "submitted": 80, "peerreview": 85, "revision": 88,
    "accepted": 95, "published": 100,
}

STAGE_COLORS = {
    "idea": "#94a3b8",       "literature": "#3b82f6",
    "methodology": "#06b6d4","datacollection": "#8b5cf6",
    "analysis": "#f97316",   "writing": "#f59e0b",
    "submitted": "#eab308",  "peerreview": "#ef4444",
    "revision": "#f87171",   "accepted": "#22c55e",
    "published": "#16a34a",
}

STAGE_BG = {
    "idea":"#f1f5f9","literature":"#eff6ff","methodology":"#ecfeff",
    "datacollection":"#f5f3ff","analysis":"#fff7ed","writing":"#fffbeb",
    "submitted":"#fefce8","peerreview":"#fef2f2","revision":"#fef2f2",
    "accepted":"#f0fdf4","published":"#f0fdf4",
}

# ── Column indices (Papers sheet, A=0) ──────────────────────────────
class COL:
    ID=0; TITLE=1; AUTHORS=2; JOURNAL=3; JTYPE=4
    STAGE=5; PRIORITY=6; PROGRESS=7
    START=8; TARGET=9; SUBMITTED=10; DECISION=11
    ACCEPTED=12; PUBLISHED=13; DOI=14
    KEYWORDS=15; COAUTHORS=16; NOTES=17; ABSTRACT=18; UPDATED=19
    TOTAL=20

PAPERS_HEADER = [
    "ID","Title","Authors","Journal Target","Journal Type",
    "Stage","Priority","Progress %","Start Date","Target Date",
    "Submitted Date","Decision Date","Accepted Date","Published Date",
    "DOI","Keywords","Co-Authors","Notes","Abstract","Last Updated",
]
ACTIVITY_HEADER = ["Timestamp","Paper ID","Action","Detail","User"]
JOURNALS_HEADER = ["Name","Impact Factor","Publisher","APC (USD)","Open Access","Scope","Notes"]

PRIORITIES = [
    ("high",   "🔴 High"),
    ("medium", "🟡 Medium"),
    ("low",    "🟢 Low"),
]
JOURNAL_TYPES = [
    "Q1 (IF > 10)","Q2 (IF 5–10)","Q3 (IF 2–5)",
    "Q4 (IF < 2)","Conference","Book Chapter",
]

DEFAULT_JOURNALS = [
    ("Nature Sustainability","25.5","Nature","11690","Optional","Sustainability science","Top-tier; landmark results only"),
    ("Energy & Environmental Science","32.5","RSC","5900","Optional","Energy + environment","Best for electrochemical/DES routes"),
    ("Green Chemistry","9.3","RSC","4400","Optional","Green processes","Great for organic acid leaching"),
    ("Chemical Engineering Journal","15.1","Elsevier","3450","Optional","Process engineering","⭐ Primary recommended target"),
    ("Journal of Cleaner Production","11.1","Elsevier","3200","Optional","Cleaner production","Ideal with LCA analysis"),
    ("Hydrometallurgy","5.4","Elsevier","2800","Optional","Hydromet processes","Most directly relevant"),
    ("Separation and Purification Technology","8.6","Elsevier","2900","Optional","Separation science","Good for selective precipitation"),
    ("Resources Conservation & Recycling","13.2","Elsevier","3100","Optional","Recycling & circular economy","Good for BD urban mining context"),
    ("Journal of Power Sources","9.2","Elsevier","3000","Optional","Battery materials","Good if cathode regen included"),
    ("Waste Management","8.3","Elsevier","2700","Optional","Waste & urban mining","Accessible; good for BD context"),
    ("Journal of Hazardous Materials","13.6","Elsevier","2900","Optional","Hazardous waste","Good if env analysis is strong"),
    ("ACS Sustainable Chemistry & Engineering","8.4","ACS","3500","Optional","Sustainable processes","Target for DES or green routes"),
    ("Bioresource Technology","11.4","Elsevier","2800","Optional","Biological processes","Use for bioleaching paper"),
    ("Metals (MDPI)","2.9","MDPI","2200","Full OA","All metal extraction","Backup — higher acceptance rate"),
]
