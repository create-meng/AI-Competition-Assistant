from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse



def _is_http_url(value: Optional[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _normalize_url(value: Optional[str]) -> Optional[str]:
    """规范化URL，自动补全协议"""
    if not isinstance(value, str) or not value.strip():
        return None

    url = value.strip()

    if url.startswith(("http://", "https://")):
        return url if _is_http_url(url) else None

    if "." in url and not url.startswith(("mailto:", "tel:", "ftp:")):
        https_url = f"https://{url}"
        if _is_http_url(https_url):
            return https_url

        http_url = f"http://{url}"
        if _is_http_url(http_url):
            return http_url

    return None


def _normalize_date(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None

    s = value.strip()
    invalid_values = ["暂无", "null", "undefined", "N/A", "n/a", "无", "待定", "未定", "-"]
    if s in invalid_values or s == "":
        return None

    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    match = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    match = re.match(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})$", s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    match = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日?$", s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # YYYY年MM月（补为月末）/ YYYY-MM（补为月末）
    match = re.match(r"^(\d{4})年(\d{1,2})月$", s)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if month == 12:
            last_day = 31
        else:
            from datetime import date

            next_month = date(year, month + 1, 1)
            last_day = (next_month - date(year, month, 1)).days
        return f"{year}-{str(month).zfill(2)}-{str(last_day).zfill(2)}"

    match = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if month == 12:
            last_day = 31
        else:
            from datetime import date

            next_month = date(year, month + 1, 1)
            last_day = (next_month - date(year, month, 1)).days
        return f"{year}-{str(month).zfill(2)}-{str(last_day).zfill(2)}"

    return s


def _normalize_contact_info(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return value

    s = value.strip()
    if not s:
        return None

    if ";" in s or "；" in s:
        parts = re.split(r"[;；]", s)
        cleaned = [p.strip() for p in parts if p.strip()]
        return "; ".join(cleaned) if cleaned else None

    if "\n" in s:
        parts = s.split("\n")
        cleaned = [p.strip() for p in parts if p.strip()]
        if len(cleaned) > 1:
            return "; ".join(cleaned)

    if "," in s or "，" in s:
        parts = re.split(r"[,，]", s)
        valid_parts = []
        for p in parts:
            p = p.strip()
            if p and not re.match(r"^\d+$", p):
                valid_parts.append(p)
        if len(valid_parts) > 1:
            return "; ".join(valid_parts)

    phone_pattern = r"(\d{11}|\d{3,4}[-\s]?\d{7,8})"
    phones = re.findall(phone_pattern, s)

    email_pattern = r"([\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,})"
    emails = re.findall(email_pattern, s)

    qq_pattern = r"QQ[群]?[：:\s]*(\d{5,12})"
    qqs = re.findall(qq_pattern, s, re.IGNORECASE)

    if len(phones) + len(emails) + len(qqs) > 1:
        name_phone_pattern = r"([^\d\s,，;；]{2,5})\s*(\d{11})"
        name_phone_matches = re.findall(name_phone_pattern, s)

        if name_phone_matches:
            parts: list[str] = []
            for name, phone in name_phone_matches:
                parts.append(f"{name.strip()} {phone}")

            for email in emails:
                email_with_label = re.search(
                    rf"([\u4e00-\u9fa5]*邮箱[：:]\s*)?{re.escape(email)}", s
                )
                if email_with_label and email_with_label.group(1):
                    parts.append(f"{email_with_label.group(1).strip()}{email}")
                else:
                    parts.append(f"邮箱: {email}")

            for qq in qqs:
                qq_with_label = re.search(rf"(QQ[群]?[：:]\s*){qq}", s, re.IGNORECASE)
                if qq_with_label:
                    parts.append(f"{qq_with_label.group(0)}")
                else:
                    parts.append(f"QQ: {qq}")

            if parts:
                return "; ".join(parts)

    return s


def _normalize_extracted_urls(data: dict[str, Any], source_url: Optional[str]) -> dict[str, Any]:
    data = dict(data or {})

    contest = data.get("contest", {}) if isinstance(data.get("contest"), dict) else {}
    dates = data.get("dates", {}) if isinstance(data.get("dates"), dict) else {}
    evaluation = data.get("evaluation", {}) if isinstance(data.get("evaluation"), dict) else {}
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}
    computed = data.get("computed", {}) if isinstance(data.get("computed"), dict) else {}

    entrant_url = _normalize_url(contest.get("entrant_url") or data.get("entrant_url"))
    teacher_url = _normalize_url(contest.get("teacher_url") or data.get("teacher_url"))
    default_url = _normalize_url(contest.get("default_url") or data.get("default_url"))

    valid_urls = [u for u in [default_url, entrant_url, teacher_url] if u is not None]
    primary_url = valid_urls[0] if valid_urls else _normalize_url(source_url)

    notes_appends: list[str] = []
    if not (default_url and entrant_url and teacher_url):
        if primary_url:
            if not default_url:
                default_url = primary_url
            if not entrant_url:
                entrant_url = primary_url
            if not teacher_url:
                teacher_url = primary_url
            notes_appends.append(
                f"未分别提取到独立入口，已将默认官网/参赛入口/教师入口统一为: {primary_url}"
            )
        else:
            notes_appends.append("未能识别任何有效的官方网站URL")

    raw_contact = contact.get("contact_info") or data.get("contact_info")
    contact_info = _normalize_contact_info(raw_contact)

    prize_info = evaluation.get("prize_info") or data.get("prize_info")

    raw_deadline = dates.get("deadline") or data.get("deadline")
    deadline = _normalize_date(raw_deadline)

    name = contest.get("name") or data.get("name")
    organizer = contest.get("organizer") or data.get("organizer")

    requirements: list[str] = []
    raw_requirements = data.get("requirements")
    if isinstance(raw_requirements, list):
        requirements = [r for r in raw_requirements if isinstance(r, str) and r.strip()]
    elif isinstance(raw_requirements, dict):
        if raw_requirements.get("eligibility"):
            requirements.extend([r for r in raw_requirements["eligibility"] if isinstance(r, str)])
        if raw_requirements.get("technical"):
            requirements.extend([r for r in raw_requirements["technical"] if isinstance(r, str)])
        if raw_requirements.get("compliance"):
            requirements.extend([r for r in raw_requirements["compliance"] if isinstance(r, str)])
    elif isinstance(raw_requirements, str) and raw_requirements.strip():
        requirements = [r.strip() for r in raw_requirements.split(",") if r.strip()]

    existing_notes = computed.get("notes") or data.get("notes") or ""
    combined_notes = "；".join([x for x in [existing_notes] if x] + notes_appends) if notes_appends else existing_notes

    result: dict[str, Any] = {
        "name": name,
        "organizer": organizer,
        "default_url": default_url,
        "entrant_url": entrant_url,
        "teacher_url": teacher_url,
        "deadline": deadline,
        "requirements": requirements,
        "contact_info": contact_info,
        "prize_info": prize_info,
        "notes": combined_notes,
        "category": contest.get("category") or data.get("category"),
        "publish_time": _normalize_date(dates.get("publish_time") or data.get("publish_time")),
        "start_date": _normalize_date(dates.get("start_date") or data.get("start_date")),
        "team_min": data.get("team_min") or (data.get("submission", {}) or {}).get("team_limits", {}).get("min_members"),
        "team_max": data.get("team_max") or (data.get("submission", {}) or {}).get("team_limits", {}).get("max_members"),
        "contest": contest,
        "dates": dates,
        "submission": data.get("submission"),
        "evaluation": evaluation,
        "contact": contact,
        "computed": computed,
    }

    return result


def calculate_confidence(extracted_data: dict[str, Any]) -> float:
    if not isinstance(extracted_data, dict):
        return 0.05

    def is_valid_url(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        normalized = _normalize_url(value)
        return normalized is not None

    def is_valid_date(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        s = value.strip()
        if re.match(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$", s):
            return True
        if re.match(r"^\d{4}年\d{1,2}月\d{1,2}日$", s):
            return True
        return False

    def has_valid_contact(value: Optional[str]) -> float:
        if not isinstance(value, str):
            return 0.0
        text = value.strip().lower()
        email_ok = re.search(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", text) is not None
        phone_ok = re.search(r"1[3-9]\d{9}", text) is not None
        if email_ok or phone_ok:
            return 1.0
        if any(k in text for k in ["qq", "wechat", "微信", "联系"]):
            return 0.5
        return 0.0

    weights = {
        "entrant_url": 0.28,
        "teacher_url": 0.22,
        "deadline": 0.20,
        "requirements": 0.15,
        "contact_info": 0.10,
        "prize_info": 0.05,
    }

    score = 0.0
    total = sum(weights.values())

    v = extracted_data.get("entrant_url")
    if is_valid_url(v):
        score += weights["entrant_url"]

    v = extracted_data.get("teacher_url")
    if is_valid_url(v):
        score += weights["teacher_url"]

    v = extracted_data.get("deadline")
    if is_valid_date(v):
        score += weights["deadline"]

    v = extracted_data.get("requirements")
    if isinstance(v, list) and len([x for x in v if isinstance(x, str) and x.strip()]) > 0:
        score += weights["requirements"]

    v = extracted_data.get("contact_info")
    score += weights["contact_info"] * has_valid_contact(v)

    if extracted_data.get("prize_info"):
        score += weights["prize_info"]

    notes = str(extracted_data.get("notes", "")).lower()
    if any(k in notes for k in ["不确定", "可能", "无法", "不清楚", "空", "null", "n/a"]):
        score *= 0.9

    confidence = max(min(score / total, 1.0), 0.0)
    if confidence == 0.0 and any(extracted_data.values()):
        confidence = 0.05
    return confidence
