"""sheets_service.py — All Google Sheets read/write operations."""

import random, string
from datetime import datetime, date
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from config import (
    SHEET_PAPERS, SHEET_ACTIVITY, SHEET_JOURNALS,
    PAPERS_HEADER, ACTIVITY_HEADER, JOURNALS_HEADER,
    DEFAULT_JOURNALS, COL, STAGE_PROGRESS, STAGES,
)


def build_service(creds_dict: dict):
    creds = Credentials(
        token=creds_dict.get("token"),
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=creds_dict.get("scopes"),
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _uid():
    return "P" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _today():
    return date.today().isoformat()


# ── Setup ─────────────────────────────────────────────────────────
def ensure_sheets(service, sid: str):
    ss = service.spreadsheets().get(spreadsheetId=sid).execute()
    existing = {s["properties"]["title"] for s in ss["sheets"]}
    missing = {SHEET_PAPERS, SHEET_ACTIVITY, SHEET_JOURNALS} - existing
    if missing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sid,
            body={"requests": [{"addSheet": {"properties": {"title": t}}} for t in missing]}
        ).execute()
    for sheet, hdr in [(SHEET_PAPERS, PAPERS_HEADER),(SHEET_ACTIVITY, ACTIVITY_HEADER),(SHEET_JOURNALS, JOURNALS_HEADER)]:
        _ensure_header(service, sid, sheet, hdr)
    if not get_all_journals(service, sid):
        _seed_journals(service, sid)

def _ensure_header(service, sid, sheet, header):
    try:
        r = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{sheet}!A1").execute()
        if not r.get("values"):
            service.spreadsheets().values().update(
                spreadsheetId=sid, range=f"{sheet}!A1",
                valueInputOption="RAW", body={"values": [header]}
            ).execute()
    except: pass

def _seed_journals(service, sid):
    service.spreadsheets().values().append(
        spreadsheetId=sid, range=f"{SHEET_JOURNALS}!A:G",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values": [list(j) for j in DEFAULT_JOURNALS]}
    ).execute()


# ── Papers CRUD ───────────────────────────────────────────────────
def get_all_papers(service, sid: str) -> list:
    try:
        r = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{SHEET_PAPERS}!A2:T").execute()
        return [_row_to_paper(row) for row in (r.get("values") or []) if row and row[0]]
    except: return []

def get_paper(service, sid: str, pid: str) -> Optional[dict]:
    return next((p for p in get_all_papers(service, sid) if p["id"] == pid), None)

def create_paper(service, sid: str, data: dict, user: str = "") -> str:
    pid = _uid()
    service.spreadsheets().values().append(
        spreadsheetId=sid, range=f"{SHEET_PAPERS}!A:T",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values": [_paper_to_row({**data, "id": pid, "last_updated": _now()})]}
    ).execute()
    _log(service, sid, pid, "created", f'Created: "{data.get("title","")}"', user)
    return pid

def update_paper(service, sid: str, pid: str, data: dict, user: str = "") -> bool:
    ri = _find_row(service, sid, SHEET_PAPERS, pid)
    if ri < 0: return False
    service.spreadsheets().values().update(
        spreadsheetId=sid, range=f"{SHEET_PAPERS}!A{ri+2}:T{ri+2}",
        valueInputOption="USER_ENTERED",
        body={"values": [_paper_to_row({**data, "id": pid, "last_updated": _now()})]}
    ).execute()
    _log(service, sid, pid, "edit", f'Updated: "{data.get("title","")}"', user)
    return True

def update_stage(service, sid: str, pid: str, new_stage: str, user: str = "") -> bool:
    p = get_paper(service, sid, pid)
    if not p: return False
    old = p["stage"]
    p["stage"] = new_stage
    p["progress"] = max(p.get("progress", 0), STAGE_PROGRESS.get(new_stage, 0))
    update_paper(service, sid, pid, p, user)
    _log(service, sid, pid, "stage_change", f"Stage: {old} → {new_stage}", user)
    return True

def delete_paper(service, sid: str, pid: str, user: str = "") -> bool:
    ri = _find_row(service, sid, SHEET_PAPERS, pid)
    if ri < 0: return False
    meta = service.spreadsheets().get(spreadsheetId=sid).execute()
    gid = next(s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == SHEET_PAPERS)
    service.spreadsheets().batchUpdate(
        spreadsheetId=sid,
        body={"requests": [{"deleteDimension": {"range": {"sheetId": gid, "dimension": "ROWS", "startIndex": ri+1, "endIndex": ri+2}}}]}
    ).execute()
    _log(service, sid, pid, "deleted", "Paper deleted", user)
    return True

def get_stats(service, sid: str) -> dict:
    papers = get_all_papers(service, sid)
    by_stage = {s["id"]: 0 for s in STAGES}
    for p in papers:
        if p["stage"] in by_stage: by_stage[p["stage"]] += 1
    in_progress_stages = ["idea","literature","methodology","datacollection","analysis","writing"]
    return {
        "papers": papers, "total": len(papers),
        "published": by_stage.get("published", 0),
        "accepted": by_stage.get("accepted", 0),
        "in_review": by_stage.get("peerreview", 0) + by_stage.get("revision", 0),
        "submitted": by_stage.get("submitted", 0),
        "in_progress": sum(by_stage.get(s, 0) for s in in_progress_stages),
        "by_stage": by_stage,
    }

# ── Activity ──────────────────────────────────────────────────────
def _log(service, sid, pid, action, detail, user=""):
    try:
        service.spreadsheets().values().append(
            spreadsheetId=sid, range=f"{SHEET_ACTIVITY}!A:E",
            valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
            body={"values": [[_now(), pid, action, detail, user]]}
        ).execute()
    except: pass

def get_activity(service, sid: str, limit=40) -> list:
    try:
        r = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{SHEET_ACTIVITY}!A2:E").execute()
        rows = list(reversed(r.get("values") or []))[:limit]
        return [{"timestamp": r[0] if len(r)>0 else "", "paper_id": r[1] if len(r)>1 else "",
                 "action": r[2] if len(r)>2 else "", "detail": r[3] if len(r)>3 else "",
                 "user": r[4] if len(r)>4 else ""} for r in rows]
    except: return []

# ── Journals ──────────────────────────────────────────────────────
def get_all_journals(service, sid: str) -> list:
    try:
        r = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{SHEET_JOURNALS}!A2:G").execute()
        return [{"name":r[0] if len(r)>0 else "","if_score":r[1] if len(r)>1 else "",
                 "publisher":r[2] if len(r)>2 else "","apc":r[3] if len(r)>3 else "",
                 "oa":r[4] if len(r)>4 else "","scope":r[5] if len(r)>5 else "",
                 "notes":r[6] if len(r)>6 else ""} for r in (r.get("values") or [])]
    except: return []

def add_journal(service, sid: str, data: dict):
    service.spreadsheets().values().append(
        spreadsheetId=sid, range=f"{SHEET_JOURNALS}!A:G",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values": [[data.get(k,"") for k in ["name","if_score","publisher","apc","oa","scope","notes"]]]}
    ).execute()

# ── Helpers ───────────────────────────────────────────────────────
def _row_to_paper(r):
    def g(i): return r[i] if i < len(r) else ""
    return {
        "id":g(COL.ID),"title":g(COL.TITLE),"authors":g(COL.AUTHORS),
        "journal":g(COL.JOURNAL),"journal_type":g(COL.JTYPE),
        "stage":g(COL.STAGE) or "idea","priority":g(COL.PRIORITY) or "medium",
        "progress":int(g(COL.PROGRESS) or 0),
        "start_date":g(COL.START),"target_date":g(COL.TARGET),
        "submitted_date":g(COL.SUBMITTED),"decision_date":g(COL.DECISION),
        "accepted_date":g(COL.ACCEPTED),"published_date":g(COL.PUBLISHED),
        "doi":g(COL.DOI),"keywords":g(COL.KEYWORDS),"co_authors":g(COL.COAUTHORS),
        "notes":g(COL.NOTES),"abstract":g(COL.ABSTRACT),"last_updated":g(COL.UPDATED),
    }

def _paper_to_row(p):
    r = [""] * COL.TOTAL
    for attr, col in [("id",COL.ID),("title",COL.TITLE),("authors",COL.AUTHORS),
        ("journal",COL.JOURNAL),("journal_type",COL.JTYPE),("stage",COL.STAGE),
        ("priority",COL.PRIORITY),("progress",COL.PROGRESS),("start_date",COL.START),
        ("target_date",COL.TARGET),("submitted_date",COL.SUBMITTED),("decision_date",COL.DECISION),
        ("accepted_date",COL.ACCEPTED),("published_date",COL.PUBLISHED),("doi",COL.DOI),
        ("keywords",COL.KEYWORDS),("co_authors",COL.COAUTHORS),("notes",COL.NOTES),
        ("abstract",COL.ABSTRACT),("last_updated",COL.UPDATED)]:
        r[col] = str(p.get(attr, ""))
    return r

def _find_row(service, sid, sheet, record_id) -> int:
    r = service.spreadsheets().values().get(spreadsheetId=sid, range=f"{sheet}!A:A").execute()
    ids = [row[0] if row else "" for row in (r.get("values") or [])]
    try: return ids.index(record_id) - 1
    except: return -1
