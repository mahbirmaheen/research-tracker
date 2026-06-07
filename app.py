"""
app.py — Research Tracker (Flask)
Vercel-ready. Uses Google Sheets as database.
All credentials come from environment variables — no local files needed on Vercel.
"""

import os, json, tempfile
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, redirect, url_for,
    session, request, flash, jsonify, abort)
from google_auth_oauthlib.flow import Flow
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

import sheets_service as svc
from config import (STAGES, STAGE_IDS, STAGE_LABELS, STAGE_ICONS,
    STAGE_PROGRESS, STAGE_COLORS, STAGE_BG, PRIORITIES, JOURNAL_TYPES, SCOPES)

load_dotenv()
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# ── Get client secrets (file on dev, env var on Vercel) ────────────
def _secrets_file():
    creds_env = os.getenv("GOOGLE_CREDENTIALS")
    if creds_env:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(creds_env); tmp.close()
        return tmp.name
    return "client_secrets.json"

# ── Template globals ───────────────────────────────────────────────
@app.context_processor
def _globals():
    return dict(
        stages=STAGES, stage_ids=STAGE_IDS, stage_labels=STAGE_LABELS,
        stage_icons=STAGE_ICONS, stage_colors=STAGE_COLORS, stage_bg=STAGE_BG,
        stage_progress=STAGE_PROGRESS, priorities=PRIORITIES, journal_types=JOURNAL_TYPES,
        current_user=session.get("user"), today=date.today().isoformat(),
    )

# ── Helpers ────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "credentials" not in session: return redirect(url_for("login"))
        return f(*a, **kw)
    return dec

def _svc():
    return svc.build_service(session["credentials"])

def _days_until(ds):
    if not ds: return None
    try: return (datetime.strptime(ds, "%Y-%m-%d").date() - date.today()).days
    except: return None

def _fmt(ds):
    if not ds: return "—"
    try: return datetime.strptime(ds, "%Y-%m-%d").strftime("%b %d, %Y")
    except: return ds

def _creds_to_dict(c):
    return {"token":c.token,"refresh_token":c.refresh_token,
            "token_uri":c.token_uri,"client_id":c.client_id,
            "client_secret":c.client_secret,"scopes":c.scopes}

app.jinja_env.filters["fmt"] = _fmt
app.jinja_env.filters["days_until"] = _days_until


# ══════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def root():
    return redirect(url_for("dashboard") if "credentials" in session else url_for("login"))

@app.route("/login")
def login():
    if "credentials" in session: return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/auth/google")
def auth_google():
    sf = _secrets_file()
    if not os.path.exists(sf):
        flash("Google credentials not configured. See setup guide.", "error")
        return redirect(url_for("login"))
    flow = Flow.from_client_secrets_file(sf, scopes=SCOPES,
        redirect_uri=url_for("auth_callback", _external=True))
    url, state = flow.authorization_url(access_type="offline",
        include_granted_scopes="true", prompt="select_account")
    session["oauth_state"] = state
    return redirect(url)

@app.route("/auth/callback")
def auth_callback():
    sf = _secrets_file()
    flow = Flow.from_client_secrets_file(sf, scopes=SCOPES,
        state=session.get("oauth_state"),
        redirect_uri=url_for("auth_callback", _external=True))
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session["credentials"] = _creds_to_dict(creds)

    import google.oauth2.credentials as g_creds
    import googleapiclient.discovery as gd
    u = gd.build("oauth2","v2",
        credentials=g_creds.Credentials(token=creds.token,refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,client_id=creds.client_id,client_secret=creds.client_secret),
        cache_discovery=False).userinfo().get().execute()
    name = u.get("name","Researcher")
    session["user"] = {"name":name,"email":u.get("email",""),"picture":u.get("picture",""),
        "initials":"".join(p[0].upper() for p in name.split()[:2])}

    try: svc.ensure_sheets(_svc(), SPREADSHEET_ID)
    except HttpError as e: flash(f"Spreadsheet error: {e.reason}", "error")

    flash(f"Welcome, {name}! 👋", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════
@app.route("/dashboard")
@login_required
def dashboard():
    try:
        data     = svc.get_stats(_svc(), SPREADSHEET_ID)
        activity = svc.get_activity(_svc(), SPREADSHEET_ID, 12)
        papers   = data["papers"]
        deadlines = sorted(
            [p for p in papers if p.get("target_date") and _days_until(p["target_date"]) is not None],
            key=lambda p: _days_until(p["target_date"]))[:6]
        recent = sorted(papers, key=lambda p: p.get("last_updated",""), reverse=True)[:8]
        pipeline = {s["id"]: [p for p in papers if p["stage"]==s["id"]] for s in STAGES}
        return render_template("dashboard.html", stats=data, activity=activity,
            deadlines=deadlines, recent=recent, pipeline=pipeline, days_until=_days_until)
    except HttpError as e:
        flash(f"Could not load data: {e.reason}", "error")
        return render_template("dashboard.html", stats={}, activity=[], deadlines=[],
            recent=[], pipeline={}, days_until=_days_until)


# ══════════════════════════════════════════════════════════════════
#  PAPERS
# ══════════════════════════════════════════════════════════════════
@app.route("/papers")
@login_required
def papers_list():
    try: papers = svc.get_all_papers(_svc(), SPREADSHEET_ID)
    except: papers = []

    sf   = request.args.get("stage","all")
    pf   = request.args.get("priority","all")
    q    = request.args.get("q","").strip().lower()
    sort = request.args.get("sort","last_updated")
    d    = request.args.get("dir","desc")

    filtered = [p for p in papers if
        (sf=="all" or p["stage"]==sf) and
        (pf=="all" or p["priority"]==pf) and
        (not q or any(q in str(p.get(f,"")).lower() for f in ["title","authors","journal","keywords"]))]

    try: filtered.sort(key=lambda p: str(p.get(sort,"")), reverse=(d=="desc"))
    except: pass

    sc = {s["id"]: sum(1 for p in papers if p["stage"]==s["id"]) for s in STAGES}
    sc["all"] = len(papers)
    return render_template("papers.html", papers=filtered, total=len(papers),
        stage_filter=sf, priority_filter=pf, search=q, sort_by=sort, sort_dir=d,
        stage_counts=sc, days_until=_days_until)

@app.route("/papers/create", methods=["POST"])
@login_required
def paper_create():
    def v(k): return request.form.get(k,"").strip()
    data = {k: v(k) for k in ["title","authors","journal","journal_type","stage",
        "priority","start_date","target_date","submitted_date","decision_date",
        "accepted_date","published_date","doi","keywords","co_authors","notes","abstract"]}
    data["progress"] = int(v("progress") or 0)
    if not data["title"]: flash("Title is required.", "error"); return redirect(request.referrer or url_for("papers_list"))
    try:
        pid = svc.create_paper(_svc(), SPREADSHEET_ID, data, session.get("user",{}).get("email",""))
        flash(f'Paper added!', "success")
        return redirect(url_for("paper_detail", paper_id=pid))
    except HttpError as e:
        flash(f"Error: {e.reason}", "error"); return redirect(url_for("papers_list"))

@app.route("/paper/<paper_id>")
@login_required
def paper_detail(paper_id):
    try: paper = svc.get_paper(_svc(), SPREADSHEET_ID, paper_id)
    except HttpError as e: flash(f"Error: {e.reason}", "error"); return redirect(url_for("papers_list"))
    if not paper: abort(404)
    keywords = [k.strip() for k in paper.get("keywords","").split(",") if k.strip()]
    stage_idx = STAGE_IDS.index(paper["stage"]) if paper["stage"] in STAGE_IDS else 0
    return render_template("paper_detail.html", paper=paper, keywords=keywords,
        stage_index=stage_idx, days_until=_days_until)

@app.route("/paper/<paper_id>/update", methods=["POST"])
@login_required
def paper_update(paper_id):
    def v(k): return request.form.get(k,"").strip()
    data = {k: v(k) for k in ["title","authors","journal","journal_type","stage",
        "priority","start_date","target_date","submitted_date","decision_date",
        "accepted_date","published_date","doi","keywords","co_authors","notes","abstract"]}
    data["progress"] = int(v("progress") or 0)
    if not data["title"]: flash("Title required.","error"); return redirect(url_for("paper_detail",paper_id=paper_id))
    try:
        svc.update_paper(_svc(), SPREADSHEET_ID, paper_id, data, session.get("user",{}).get("email",""))
        flash("Paper saved! ✓", "success")
    except HttpError as e: flash(f"Error: {e.reason}", "error")
    return redirect(url_for("paper_detail", paper_id=paper_id))

@app.route("/paper/<paper_id>/delete", methods=["POST"])
@login_required
def paper_delete(paper_id):
    try:
        svc.delete_paper(_svc(), SPREADSHEET_ID, paper_id, session.get("user",{}).get("email",""))
        flash("Paper deleted.", "success")
    except HttpError as e: flash(f"Error: {e.reason}", "error")
    return redirect(url_for("papers_list"))

@app.route("/api/paper/<paper_id>/stage", methods=["POST"])
@login_required
def api_stage(paper_id):
    ns = request.json.get("stage")
    if ns not in STAGE_IDS: return jsonify({"ok":False,"error":"Invalid"}), 400
    try:
        svc.update_stage(_svc(), SPREADSHEET_ID, paper_id, ns, session.get("user",{}).get("email",""))
        p = svc.get_paper(_svc(), SPREADSHEET_ID, paper_id)
        return jsonify({"ok":True,"stage":ns,"progress":p.get("progress",0)})
    except HttpError as e: return jsonify({"ok":False,"error":str(e.reason)}), 500

@app.route("/api/paper/<paper_id>/progress", methods=["POST"])
@login_required
def api_progress(paper_id):
    prog = int(request.json.get("progress", 0))
    try:
        p = svc.get_paper(_svc(), SPREADSHEET_ID, paper_id)
        if not p: return jsonify({"ok":False}), 404
        p["progress"] = prog
        svc.update_paper(_svc(), SPREADSHEET_ID, paper_id, p, session.get("user",{}).get("email",""))
        return jsonify({"ok":True,"progress":prog})
    except HttpError as e: return jsonify({"ok":False,"error":str(e.reason)}), 500


# ══════════════════════════════════════════════════════════════════
#  JOURNALS
# ══════════════════════════════════════════════════════════════════
@app.route("/journals")
@login_required
def journals_list():
    try: journals = svc.get_all_journals(_svc(), SPREADSHEET_ID)
    except: journals = []
    q = request.args.get("q","").strip().lower()
    if q: journals = [j for j in journals if q in (j.get("name","")+j.get("scope","")+j.get("publisher","")).lower()]
    return render_template("journals.html", journals=journals, search=q)

@app.route("/journals/add", methods=["POST"])
@login_required
def journal_add():
    def v(k): return request.form.get(k,"").strip()
    data = {k: v(k) for k in ["name","if_score","publisher","apc","oa","scope","notes"]}
    if not data["name"]: flash("Name required.", "error"); return redirect(url_for("journals_list"))
    try: svc.add_journal(_svc(), SPREADSHEET_ID, data); flash(f'Journal "{data["name"]}" added!', "success")
    except HttpError as e: flash(f"Error: {e.reason}", "error")
    return redirect(url_for("journals_list"))


# ══════════════════════════════════════════════════════════════════
#  TIMELINE
# ══════════════════════════════════════════════════════════════════
@app.route("/timeline")
@login_required
def timeline():
    try: papers = svc.get_all_papers(_svc(), SPREADSHEET_ID)
    except: papers = []
    tl = sorted([p for p in papers if p.get("target_date") or p.get("start_date")],
        key=lambda p: p.get("target_date") or p.get("start_date",""))
    gantt = [p for p in papers if p.get("start_date") and p.get("target_date")][:15]
    gantt_data, gantt_meta = [], {}
    if gantt:
        from datetime import datetime as dt
        all_d = []
        for p in gantt:
            for ds in [p["start_date"], p["target_date"]]:
                try: all_d.append(dt.strptime(ds, "%Y-%m-%d"))
                except: pass
        if all_d:
            mn, mx = min(all_d), max(all_d)
            span = (mx - mn).days or 1
            tp = min(100, max(0, ((dt.now()-mn).days/span)*100))
            for p in gantt:
                try:
                    s = dt.strptime(p["start_date"],"%Y-%m-%d")
                    t = dt.strptime(p["target_date"],"%Y-%m-%d")
                    gantt_data.append({**p,
                        "bar_left": round(((s-mn).days/span)*100,1),
                        "bar_width": max(1, round(((t-s).days/span)*100,1)),
                        "bar_color": STAGE_COLORS.get(p["stage"],"#94a3b8")})
                except: pass
            gantt_meta = {"min_label":mn.strftime("%b %Y"),"max_label":mx.strftime("%b %Y"),"today_pct":tp}
    return render_template("timeline.html", tl_papers=tl, gantt_data=gantt_data,
        gantt_meta=gantt_meta, days_until=_days_until)


# ══════════════════════════════════════════════════════════════════
#  ERRORS
# ══════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV","development") == "development"
    print(f"\n🔬 Research Tracker → http://localhost:{port}")
    print(f"   Spreadsheet: {SPREADSHEET_ID or '⚠ NOT SET'}")
    print(f"   Secrets file: {'✓' if os.path.exists('client_secrets.json') else '⚠ NOT FOUND'}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
