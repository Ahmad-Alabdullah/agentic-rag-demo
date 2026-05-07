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
    # XML einlesen; bei korrupten oder leeren Dateien wird eine leere Liste zurückgegeben
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Fehler beim Parsen von {xml_path}: {e}")
        return []

    # Neuere Protokoll-Formate kodieren Metadaten als Root-Attribute (z. B. sitzung-nr="100"),
    # ältere Formate als Textelemente (z. B. <sitzungsnr>100</sitzungsnr>).
    # Daher: zuerst Attribut prüfen, dann Kindelement als Fallback.
    session_number = root.get("sitzung-nr") or root.findtext(".//sitzungsnr") or ""
    session_date = root.get("sitzung-datum") or root.findtext(".//datum") or ""
    wahlperiode = root.get("wahlperiode") or root.findtext(".//wahlperiode") or ""

    redebeitraege = []

    # Alle Tagesordnungspunkte suchen. Manche Protokoll-Typen (z. B. Sondersitzungen)
    # haben keine <tagesordnungspunkt>-Elemente — dann gilt das gesamte Dokument als ein TOP.
    tops = root.findall(".//tagesordnungspunkt")
    if not tops:
        tops = [root]

    for top in tops:
        # Verschiedene Protokoll-Generationen verwenden entweder top-id oder id als Attributname
        top_nr = top.get("top-id") or top.get("id") or ""
        top_titel = _extract_top_titel(top)

        for rede in top.findall(".//rede"):
            rede_id = rede.get("id") or ""

            redner_el = rede.find(".//redner")
            # Beiträge ohne <redner>-Element (z. B. manche Präsidentenformeln) überspringen
            if redner_el is None:
                continue

            vorname = redner_el.findtext(".//vorname") or ""
            nachname = redner_el.findtext(".//nachname") or ""
            fraktion = redner_el.findtext(".//fraktion") or ""
            rolle = redner_el.findtext(".//rolle_lang") or redner_el.findtext(".//rolle") or ""

            text = _extract_speech_text(rede)

            # Zu kurze Texte (< 50 Zeichen) sind meist leere Formeln ohne inhaltlichen Wert
            # für das Retrieval und werden daher verworfen
            if not text.strip() or len(text) < 50:
                continue

            redebeitraege.append({
                # Wenn die XML-ID fehlt, eindeutige Fallback-ID aus Sitzungsnummer + laufendem Index
                "rede_id": rede_id or f"{session_number}_{len(redebeitraege)}",
                "speaker_full": f"{vorname} {nachname}".strip(),
                "vorname": vorname,
                "nachname": nachname,
                # _clean() normalisiert Non-breaking Spaces (\xa0), die im XML häufig vorkommen
                # und sonst Metadaten-Filter im Retrieval brechen würden
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
    """
    Probiert mehrere XPaths der Reihe nach und gibt den ersten nicht-leeren Treffer zurück.
    Hilfsfunktion für XML-Schemata, die denselben Inhalt unter verschiedenen Pfaden ablegen.
    """
    for xpath in xpaths:
        result = el.findtext(xpath)
        if result and result.strip():
            return result.strip()
    return ""


def _extract_top_titel(top_el) -> str:
    """Extrahiert den Titel — sucht nur in <p>-Elementen außerhalb von <rede>."""
    # Reihenfolge nach Priorität: T_Beratung ist die primäre Klasse für TOP-Überschriften
    # im aktuellen XML-Format; T_fett und T_Drs sind Fallbacks für ältere Formate
    for klasse in ("T_Beratung", "T_fett", "T_Drs"):
        # not(ancestor::rede) schließt <p>-Elemente innerhalb von Reden aus,
        # damit keine Zitate oder Redepassagen fälschlich als Titel erkannt werden
        results = top_el.xpath(f".//p[@klasse='{klasse}'][not(ancestor::rede)]")
        if results and results[0].text:
            # Auf 200 Zeichen begrenzen, um ChromaDB-Metadaten-Felder nicht zu überlasten
            return results[0].text.strip()[:200]
    return ""


def _extract_speech_text(rede_el) -> str:
    """
    Extrahiert den Redetext, filtert Redner-Angaben heraus
    und kennzeichnet Zwischenrufe.
    """
    parts = []

    # .//p findet alle Absätze unabhängig von ihrer Tiefe im Element-Baum
    for p in rede_el.findall(".//p"):
        klasse = p.get("klasse", "")

        # Klassen "redner" und "MdB" markieren die Rednerankündigung (Name, Fraktion),
        # nicht den eigentlichen Redeinhalt — diese Absätze werden übersprungen
        if klasse in ("redner", "MdB"):
            continue

        # Zwischenrufe ("J_1" im aktuellen Format, "zwischenruf" in älteren) werden
        # als "[Zwischenruf: …]" in den Text eingebettet statt verworfen,
        # damit Suchanfragen nach Reaktionen auf Reden diese finden können
        if klasse == "J_1" or "zwischenruf" in klasse.lower():
            text = "".join(p.itertext()).strip()
            if text:
                parts.append(f"[Zwischenruf: {text}]")
            continue

        # itertext() holt den Text aus verschachtelten Kindelementen (z. B. <a>, <b>)
        # und fügt ihn ohne XML-Tags zusammen
        text = "".join(p.itertext()).strip()
        if text:
            parts.append(text)

    # Doppelter Zeilenumbruch als Absatztrenner — konsistent mit text.split("\n\n")
    # im Indexer, der diesen Trenner zum Chunk-Splitting verwendet
    return "\n\n".join(parts)


def parse_all_protocols(data_dir: str) -> List[Dict]:
    """Parst alle XML-Dateien im Verzeichnis."""
    # glob("*.xml") erfasst nur XML-Dateien direkt im Verzeichnis, keine Unterordner
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
