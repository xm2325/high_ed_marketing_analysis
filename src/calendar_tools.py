from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
import pandas as pd

CALENDAR_REQUIRED = [
    "start_date", "end_date", "event", "population", "audience", "phase",
    "channel", "owner_team", "primary_kpi", "recommended_action", "date_type", "source_id"
]


def normalise_calendar(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in CALENDAR_REQUIRED:
        if col not in out.columns:
            out[col] = ""
    out["start_date"] = pd.to_datetime(out["start_date"], errors="coerce")
    out["end_date"] = pd.to_datetime(out["end_date"], errors="coerce")
    out["end_date"] = out["end_date"].fillna(out["start_date"])
    out = out.dropna(subset=["start_date", "event"]).copy()
    out["display_end"] = out["end_date"] + pd.Timedelta(days=1)
    return out.sort_values(["start_date", "event"]).reset_index(drop=True)


def build_utm_url(base_url: str, source: str, medium: str, campaign: str, content: str = "", term: str = "") -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({"utm_source": source, "utm_medium": medium, "utm_campaign": campaign})
    if content:
        query["utm_content"] = content
    if term:
        query["utm_term"] = term
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def calendar_to_ics(df: pd.DataFrame, calendar_name: str = "Recruitment Campaign Calendar") -> bytes:
    normalised = normalise_calendar(df)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Portfolio Prototype//Recruitment Calendar//EN", f"X-WR-CALNAME:{_escape(calendar_name)}"]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for idx, row in normalised.iterrows():
        start = pd.Timestamp(row["start_date"]).strftime("%Y%m%d")
        # all-day ICS end date is exclusive
        end = (pd.Timestamp(row["end_date"]) + pd.Timedelta(days=1)).strftime("%Y%m%d")
        description = f"Audience: {row['audience']}\\nPhase: {row['phase']}\\nChannel: {row['channel']}\\nOwner: {row['owner_team']}\\nKPI: {row['primary_kpi']}\\nAction: {row['recommended_action']}\\nSource: {row['source_id']}"
        uid = f"recruitment-calendar-{idx}-{start}@portfolio.local"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            f"SUMMARY:{_escape(str(row['event']))}",
            f"DESCRIPTION:{_escape(description)}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def next_event(df: pd.DataFrame, today: date | None = None) -> pd.Series | None:
    today = today or date.today()
    cal = normalise_calendar(df)
    future = cal[cal["end_date"].dt.date >= today]
    if future.empty:
        return None
    return future.iloc[0]
