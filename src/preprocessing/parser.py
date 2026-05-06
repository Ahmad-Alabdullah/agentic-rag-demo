"""
XML-Parser für Bundestags-Plenarprotokolle.
Extrahiert Redebeiträge mit vollständigen Metadaten.
"""

from lxml import etree
from typing import List, Dict
from pathlib import Path


def parse_plenarprotokoll(xml_path: str) -> List[Dict]:
    """
    Parst ein Bundestags-Plenarprotokoll-XML.

    Gibt eine Liste von Redebeiträgen zurück, jeder mit:
    - text: Volltext der Rede
    - speaker_full, vorname, nachname, fraktion, rolle
    - session_number, session_date, wahlperiode
    - top_nr, top_titel, rede_id
    """
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Fehler beim Parsen von {xml_path}: {e}")
        return []

    # Sitzungs-Metadaten bevorzugt aus Root-Attributen lesen
    session_number = root.get("sitzung-nr") or root.findtext(".//sitzungsnr") or ""
    session_date = root.get("sitzung-datum") or root.findtext(".//datum") or ""
    wahlperiode = root.get("wahlperiode") or root.findtext(".//wahlperiode") or ""

    redebeitraege = []

    tops = root.findall(".//tagesordnungspunkt")
    if not tops:
        tops = [root]

    for top in tops:
        top_nr = top.get("top-id") or top.get("id") or ""
        top_titel = _extract_top_titel(top)

        for rede in top.findall(".//rede"):
            rede_id = rede.get("id") or ""

            redner_el = rede.find(".//redner")
            if redner_el is None:
                continue

            vorname = redner_el.findtext(".//vorname") or ""
            nachname = redner_el.findtext(".//nachname") or ""
            fraktion = redner_el.findtext(".//fraktion") or ""
            rolle = redner_el.findtext(".//rolle_lang") or redner_el.findtext(".//rolle") or ""

            text = _extract_speech_text(rede)

            if not text.strip() or len(text) < 50:
                continue

            redebeitraege.append({
                "rede_id": rede_id or f"{session_number}_{len(redebeitraege)}",
                "speaker_full": f"{vorname} {nachname}".strip(),
                "vorname": vorname,
                "nachname": nachname,
                "fraktion": _clean(fraktion),
                "rolle": rolle,
                "session_number": session_number,
                "session_date": session_date,
                "wahlperiode": wahlperiode,
                "top_nr": _clean(top_nr),
                "top_titel": _clean(top_titel),
                "text": text,
                "source_file": Path(xml_path).name,
            })

    print(f"  {Path(xml_path).name}: {len(redebeitraege)} Redebeiträge extrahiert")
    return redebeitraege


def _clean(text: str) -> str:
    """Ersetzt non-breaking spaces und normalisiert Whitespace."""
    return text.replace("\xa0", " ").strip()


def _find_text(el, xpaths: List[str]) -> str:
    for xpath in xpaths:
        result = el.findtext(xpath)
        if result and result.strip():
            return result.strip()
    return ""


def _extract_top_titel(top_el) -> str:
    """Extrahiert den Titel — sucht nur in <p>-Elementen außerhalb von <rede>."""
    for klasse in ("T_Beratung", "T_fett", "T_Drs"):
        results = top_el.xpath(f".//p[@klasse='{klasse}'][not(ancestor::rede)]")
        if results and results[0].text:
            return results[0].text.strip()[:200]
    return ""


def _extract_speech_text(rede_el) -> str:
    """
    Extrahiert den Redetext, filtert Redner-Angaben heraus
    und kennzeichnet Zwischenrufe.
    """
    parts = []

    for p in rede_el.findall(".//p"):
        klasse = p.get("klasse", "")

        if klasse in ("redner", "MdB"):
            continue

        if klasse == "J_1" or "zwischenruf" in klasse.lower():
            text = "".join(p.itertext()).strip()
            if text:
                parts.append(f"[Zwischenruf: {text}]")
            continue

        text = "".join(p.itertext()).strip()
        if text:
            parts.append(text)

    return "\n\n".join(parts)


def parse_all_protocols(data_dir: str) -> List[Dict]:
    """Parst alle XML-Dateien im Verzeichnis."""
    xml_files = list(Path(data_dir).glob("*.xml"))

    if not xml_files:
        print(f"Keine XML-Dateien in {data_dir} gefunden.")
        return []

    print(f"Gefunden: {len(xml_files)} XML-Dateien")
    all_speeches = []

    for xml_file in xml_files:
        speeches = parse_plenarprotokoll(str(xml_file))
        all_speeches.extend(speeches)

    print(f"Gesamt: {len(all_speeches)} Redebeiträge")
    return all_speeches
