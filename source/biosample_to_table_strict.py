
#!/usr/bin/env python3
"""
Build a strict, order-preserving table from a list of BioSample accessions (SAMN… or SAMEA…).

For each input accession:
  - ESearch (db=biosample) to get UID(s).
  - EFetch by UID (XML).
  - Verify XML BioSample accession == input accession.
  - Write row only if verified; otherwise log mismatch/not found.

Outputs:
  - biosample_table.tsv                   : verified rows (TSV)
  - biosample_resolution_report.tsv       : per-input resolution status (UIDs found, match/mismatch)
  - biosample_xml_cache/<accession>.xml   : cached XML per accession (optional, useful for debugging)

Usage:
  python biosample_to_table_strict.py \
    --email 'your.email@example.org' \
    --input accessions.txt \
    --out biosample_table.tsv \
    [--api-key YOUR_NCBI_API_KEY] \
    [--cache-xml] \
    [--sleep 0.4]
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from Bio import Entrez  # Biopython

# -------------------- pacing per NCBI guidelines --------------------
def pace(sleep_sec: float):
    time.sleep(max(0.0, sleep_sec))

# -------------------- E-utilities helpers --------------------

def esearch_uids_for_accession(accession: str) -> list[str]:
    """Return UIDs for an accession via ESearch, parsing XML with Entrez.read()."""
    with Entrez.esearch(
        db="biosample",
        term=f'{accession}[All Fields]',
        retmode="xml",     # <-- XML, not JSON
        retmax=100
    ) as h:
        data = Entrez.read(h)  # <-- Biopython parses XML into a Python dict
    ids = data.get("IdList") or []
    return list(ids)


def efetch_biosample_xml_by_uid(uid: str) -> str:
    with Entrez.efetch(db="biosample", id=str(uid), retmode="xml") as h:
        return h.read()

def parse_biosample_record(xml_text: str) -> Optional[Dict]:
    """Parse a single BioSample from XML text into a dict of fields."""
    if not xml_text.strip():
        return None
    root = ET.fromstring(xml_text)
    bs = root.find(".//BioSample")
    if bs is None:
        return None
    rec = {
        "biosample_accession": bs.get("accession") or "",
        "ncbi_uid": bs.get("id") or "",
        "title": None,
        "organism_name": None,
        "taxonomy_id": None,
        "submission_date": bs.get("submission_date"),
        "publication_date": bs.get("publication_date"),
        "last_update": bs.get("last_update"),
        "sra_cross_id": None,
        "package": None,
        "attributes": {}
    }
    # Description and Organism
    desc = bs.find("Description")
    if desc is not None:
        rec["title"] = desc.findtext("Title")
        organism = desc.find("Organism")
    else:
        organism = bs.find("Organism")
    if organism is not None:
        rec["organism_name"] = organism.get("taxonomy_name")
        rec["taxonomy_id"] = organism.get("taxonomy_id")
    # Package
    pkg = bs.find("Package")
    rec["package"] = pkg.text if pkg is not None else None
    # SRA cross-id (ERS/SRS/etc.)
    for idn in bs.findall(".//Ids/Id"):
        if idn.get("db") == "SRA":
            val = (idn.text or "").strip()
            if val:
                rec["sra_cross_id"] = val
                break
    # Attributes (harmonized preferred)
    for a in bs.findall(".//Attributes/Attribute"):
        k = a.get("harmonized_name") or a.get("attribute_name") or a.get("display_name") or "attribute"
        v = (a.text or "").strip()
        if k in rec["attributes"] and rec["attributes"][k] != v:
            rec["attributes"][k] += f";{v}"
        else:
            rec["attributes"][k] = v
    return rec

# -------------------- main --------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True, help="Email for NCBI Entrez")
    ap.add_argument("--api-key", default=None, help="NCBI API key (optional)")
    ap.add_argument("--input", required=True, help="Text file: one BioSample accession per line (SAMN… or SAMEA…)")
    ap.add_argument("--out", default="biosample_table.tsv", help="Output TSV path")
    ap.add_argument("--report", default="biosample_resolution_report.tsv", help="Resolution report TSV path")
    ap.add_argument("--sleep", type=float, default=0.40, help="Sleep between requests (seconds)")
    ap.add_argument("--cache-xml", action="store_true", help="Cache fetched XML per accession")
    args = ap.parse_args()

    Entrez.email = args.email
    if args.api_key:
        Entrez.api_key = args.api_key
        # Allow faster pacing if API key is present
        if args.sleep < 0.12:
            args.sleep = 0.12

    in_path = Path(args.input)
    out_path = Path(args.out)
    rep_path = Path(args.report)
    xml_cache_dir = Path("biosample_xml_cache")
    if args.cache_xml:
        xml_cache_dir.mkdir(exist_ok=True)

    # Read accessions (preserve order, drop blanks)
    with open(in_path, "r", encoding="utf-8") as f:
        accessions = [line.strip() for line in f if line.strip()]

    # Prepare outputs
    table_header = [
        "biosample_accession",
        "ncbi_uid",
        "title",
        "organism_name",
        "taxonomy_id",
        "submission_date",
        "publication_date",
        "last_update",
        "sra_cross_id",
        "package",
        "attributes_json"
    ]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter="\t").writerow(table_header)

    with open(rep_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["input_accession", "uids_found", "matched_uid", "status", "note"])

    # Process each accession strictly
    for acc in accessions:
        try:
            uids = esearch_uids_for_accession(acc)
            pace(args.sleep)
        except Exception as e:
            with open(rep_path, "a", encoding="utf-8", newline="") as f:
                csv.writer(f, delimiter="\t").writerow([acc, 0, "", "error", f"ESearch failed: {e}"])
            continue

        if not uids:
            with open(rep_path, "a", encoding="utf-8", newline="") as f:
                csv.writer(f, delimiter="\t").writerow([acc, 0, "", "not_found", "No UID from ESearch"])
            continue

        # Try each UID until we find an XML record whose accession matches the input
        matched_rec = None
        matched_uid = ""
        note = ""
        for uid in uids:
            try:
                xml = efetch_biosample_xml_by_uid(uid)
                pace(args.sleep)
                rec = parse_biosample_record(xml)
            except Exception as e:
                note = f"EFetch/parse failed for UID {uid}: {e}"
                continue

            if args.cache_xml:
                (xml_cache_dir / f"{acc}_{uid}.xml").write_text(xml, encoding="utf-8")

            if rec and rec["biosample_accession"] == acc:
                matched_rec = rec
                matched_uid = uid
                break

        status = "matched" if matched_rec else "mismatch"
        with open(rep_path, "a", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="\t").writerow([acc, len(uids), matched_uid, status, note])

        if not matched_rec:
            # Strict: do not write table row if XML accession != input accession
            continue

        # Write verified row
        row = [
            matched_rec.get("biosample_accession", ""),
            matched_rec.get("ncbi_uid", ""),
            matched_rec.get("title") or "",
            matched_rec.get("organism_name") or "",
            matched_rec.get("taxonomy_id") or "",
            matched_rec.get("submission_date") or "",
            matched_rec.get("publication_date") or "",
            matched_rec.get("last_update") or "",
            matched_rec.get("sra_cross_id") or "",
            matched_rec.get("package") or "",
            json.dumps(matched_rec.get("attributes", {}), ensure_ascii=False),
        ]
        with open(out_path, "a", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="\t").writerow(row)

    print(f"[DONE] Verified table: {out_path}", file=sys.stderr)
    print(f"[DONE] Resolution report: {rep_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
