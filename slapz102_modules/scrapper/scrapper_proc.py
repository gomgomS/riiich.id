import sys
import re
import traceback
import requests
from bs4 import BeautifulSoup

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

STOP_MARKERS = ["Pergi Ke Pelajaran", "Bagikan ke", "ben.Adam"]

def _extract_day_label(url):
    """e.g. .../1-mei-2026/ → '1 Mei 2026'"""
    slug  = url.rstrip("/").split("/")[-1]
    parts = slug.split("-")
    if len(parts) == 3:
        return f"{parts[0]} {parts[1].capitalize()} {parts[2]}"
    # end if
    return slug
# end def

def _extract_url_meta(url):
    """
    Parse year, triwulan, pelajaran_no from the URL.
    Pattern: .../triwulan-2-2026-pelajaran-4/...
    """
    m = re.search(r"triwulan-(\d+)-(\d{4})-pelajaran-(\d+)", url)
    if m:
        return {
            "triwulan"    : int(m.group(1)),
            "year"        : int(m.group(2)),
            "pelajaran_no": int(m.group(3)),
        }
    # end if
    return { "triwulan": 0, "year": 0, "pelajaran_no": 0 }
# end def

def _classify(raw):
    """Classify a paragraph string into a content type."""
    if re.match(r"Untuk Pelajaran", raw, re.IGNORECASE):
        return "bacaan"
    elif re.match(r"AYAT HAFALAN", raw, re.IGNORECASE):
        return "ayat_hafalan"
    elif re.match(r"(Bacalah|Bagaimanakah|Apakah|Mengapa|Renungkan)", raw, re.IGNORECASE):
        return "question"
    # end if
    return "paragraph"
# end def

def _parse_ps(p_elements):
    """Turn a list of <p> BS4 elements into structured dicts."""
    result = []
    for p in p_elements:
        raw = re.sub(r"\s+", " ", p.get_text(separator=" ", strip=True)).strip()
        if raw:
            result.append({ "type": _classify(raw), "text": raw })
        # end if
    # end for
    return result
# end def

def _fetch_sabtu_title(sabtu_url):
    """
    Quick-fetch the Sabtu page and return its lesson title
    (first <a align="justify"><b>TEXT</b></a>).
    """
    try:
        resp  = requests.get(sabtu_url, headers=HEADERS, timeout=10)
        soup  = BeautifulSoup(resp.text, "html.parser")
        anch  = soup.find_all("a", attrs={"align": "justify"})
        if anch:
            bold = anch[0].find("b")
            if bold:
                return bold.get_text(strip=True)
            # end if
        # end if
        return ""
    except Exception:
        return ""
    # end try
# end def

def scrape_sekolah_sabat(url):
    """
    Works for ALL day pages (Sabtu – Jumat).
    1. Title  — first  <a align="justify"><b>TEXT</b></a>
    2. Content — all <p> after that anchor via find_all_next,
       stopping at navigation markers.
    """
    try:
        resp = requests.get(url.strip(), headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        anchors = soup.find_all("a", attrs={"align": "justify"})

        # ── Title ──
        title = ""
        if anchors:
            bold = anchors[0].find("b")
            if bold:
                title = bold.get_text(strip=True)
            # end if
        # end if

        # ── Content ──
        # Strategy 1: find_all_next("p") from first align=justify anchor
        # Strategy 2 (fallback): find_all_next("p") from the Download PPT link
        # — guarantees content is found even when page has no align=justify anchors.
        def _collect_ps(start_element):
            result = []
            for p in start_element.find_all_next("p"):
                raw = re.sub(r"\s+", " ", p.get_text(separator=" ", strip=True)).strip()
                if len(raw) < 10:
                    continue
                if any(m.lower() in raw.lower() for m in STOP_MARKERS):
                    break
                link_text = " ".join(a.get_text(strip=True) for a in p.find_all("a"))
                if raw == link_text:
                    continue
                result.append(p)
            # end for
            return result
        # end def

        content_ps = []

        # Strategy 1 — align=justify anchor
        if anchors:
            content_ps = _collect_ps(anchors[0])
        # end if

        # Strategy 2 — fallback: start from the PPT/Download link
        if not content_ps:
            for a in soup.find_all("a", href=True):
                t    = a.get_text(strip=True).lower()
                href = a.get("href", "").lower()
                if ("download" in t and ("powerpoint" in t or "ppt" in t)) \
                   or "slideshare" in href or ".pptx" in href:
                    content_ps = _collect_ps(a)
                    break
                # end if
            # end for
        # end if

        content = _parse_ps(content_ps)


        # ── PPT link ──
        ppt_url = ""
        for a in soup.find_all("a", href=True):
            t    = a.get_text(strip=True).lower()
            href = a["href"].lower()
            if ("download" in t and ("powerpoint" in t or "ppt" in t)) \
               or "slideshare" in href or ".pptx" in href:
                ppt_url = a["href"]
                break
            # end if
        # end for

        # ── Day navigation ──
        day_names = ["Sabtu","Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Penuntun Guru"]
        day_nav   = []
        seen      = set()
        for a in soup.find_all("a", href=True):
            label = a.get_text(strip=True)
            if label in day_names and label not in seen:
                seen.add(label)
                day_nav.append({ "label": label, "url": a["href"] })
            # end if
        # end for

        # ── Lesson title (always from Sabtu page) ──
        # If current page IS Sabtu, lesson_title = title already.
        # Otherwise fetch Sabtu page for the definitive lesson title.
        sabtu_nav  = next((n for n in day_nav if n["label"] == "Sabtu"), None)
        is_sabtu   = sabtu_nav and sabtu_nav["url"].rstrip("/") == url.rstrip("/")
        if is_sabtu or not sabtu_nav:
            lesson_title = title
        else:
            lesson_title = _fetch_sabtu_title(sabtu_nav["url"]) or title
        # end if

        return {
            "ok"           : True,
            "day_label"    : _extract_day_label(url),
            "url_meta"     : _extract_url_meta(url),
            "title"        : title,
            "lesson_title" : lesson_title,
            "content"      : content,
            "ppt_url"      : ppt_url,
            "day_nav"      : day_nav,
            "source_url"   : url,
            "error"        : ""
        }

    except requests.exceptions.Timeout:
        return { "ok": False, "error": "Koneksi timeout. Cek URL atau coba lagi." }
    except requests.exceptions.ConnectionError:
        return { "ok": False, "error": "Tidak bisa terhubung ke URL tersebut." }
    except Exception:
        print(traceback.format_exc())
        return { "ok": False, "error": "Gagal scraping. Periksa URL dan coba lagi." }
    # end try
# end def
