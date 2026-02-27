
#!/usr/bin/env python3
"""
Fetch full SRA experiment metadata for a list of SRX/ERX accessions and save as JSON blobs.

- Input:  file with one accession per line (SRX... or ERX...), or a list on the CLI
- Output: TSV with columns [input_accession, metadata_json] and a JSONL mirror

E-utilities used:
  * esearch.fcgi?db=sra&term=<accession>
  * efetch.fcgi?db=sra&id=<uid(s)>&retmode=xml

Docs:
  - E-utilities reference & parameters: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/         (Reference Guide)  # noqa
  - SRA search & acceptance of SRX/ERX/DRX accessions in Entrez SRA:                         # noqa
    https://www.ncbi.nlm.nih.gov/sra/docs/srasearch/ (see “Search by accession”)             # noqa
"""

import argparse
import csv
import json
import os
import sys
import time
import typing as t
import xml.etree.ElementTree as ET

import requests

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"

# Default conservative throttling (NCBI guidance ~3 req/s; relax if you have an API key)
DEFAULT_SLEEP = 0.35


# ----------------------------- XML -> JSON helpers -----------------------------
def _etree_to_dict(elem: ET.Element) -> t.Dict[str, t.Any]:
    """
    Convert an ElementTree node into a nested dict:
      - attributes -> "@attr"
      - text -> "#text" (stripped)
      - children with same tag -> list
    """
    node: t.Dict[str, t.Any] = {}
    # attributes
    if elem.attrib:
        node["@attr"] = dict(elem.attrib)

    # children
    children = list(elem)
    if children:
        by_tag: t.Dict[str, t.List[t.Any]] = {}
        for c in children:
            d = _etree_to_dict(c)
            by_tag.setdefault(c.tag, []).append(d)
        # collapse singletons to single object
        for tag, items in by_tag.items():
            node[tag] = items[0] if len(items) == 1 else items
    else:
        # leaf text
        text = (elem.text or "").strip()
        if text:
            node["#text"] = text

    return node


def xml_to_json_obj(xml_text: str) -> t.Union[t.Dict[str, t.Any], t.List[t.Any], None]:
    """
    Turn the SRA XML payload into a JSON-serializable object.
    We preserve the full EXPERIMENT_PACKAGE content (no field loss).
    """
    xml_text = xml_text.strip()
    if not xml_text:
        return None
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    # Capture either single EXPERIMENT_PACKAGE or a SET of them
    if root.tag.endswith("EXPERIMENT_PACKAGE_SET"):
        pkgs = [child for child in root if child.tag.endswith("EXPERIMENT_PACKAGE")]
        return [_etree_to_dict(pkg) for pkg in pkgs]
    elif root.tag.endswith("EXPERIMENT_PACKAGE"):
        return _etree_to_dict(root)
    else:
        # Fallback: return full root tree
        return _etree_to_dict(root)


# ----------------------------- E-utilities calls -------------------------------
def esearch_sra_ids(term: str, api_key: t.Optional[str], email: t.Optional[str]) -> t.List[str]:
    """Return Entrez UIDs in SRA matching the accession/term."""
    params = {
        "db": "sra",
        "term": term,
        "retmode": "json",
        "retmax": "10000",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    r = requests.get(ESEARCH_URL, params=params, timeout=60)
    r.raise_for_status()
    js = r.json()
    return js.get("esearchresult", {}).get("idlist", [])


def efetch_sra_xml(uids: t.List[str], api_key: t.Optional[str], email: t.Optional[str]) -> str:
    """Fetch SRA XML for one or more UIDs."""
    if not uids:
        return ""
    params = {"db": "sra", "id": ",".join(uids), "retmode": "xml"}
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    r = requests.get(EFETCH_URL, params=params, timeout=120)
    r.raise_for_status()
    return r.text


# --------------------------------- CLI script ---------------------------------
def normalize_accessions(lines: t.Iterable[str]) -> t.List[str]:
    seen, out = set(), []
    for raw in lines:
        a = raw.strip().replace("\r", "")
        if not a or a in seen:
            continue
        seen.add(a)
        out.append(a)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Fetch full SRA experiment metadata for SRX/ERX accessions and save JSON blobs."
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="Text file with one accession per line (SRX... or ERX...)")
    g.add_argument("--accessions", nargs="+", help="Accessions provided on the command line")
    ap.add_argument("--out-tsv", default="sra_experiment_metadata.tsv", help="Output TSV path")
    ap.add_argument("--out-jsonl", default="sra_experiment_metadata.jsonl", help="Output JSONL path")
    ap.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"), help="NCBI API key")
    ap.add_argument("--email", default=os.environ.get("EMAIL"), help="Contact email (recommended by NCBI)")
    ap.add_argument("--sleep", type=float, default=DEFAULT_SLEEP, help="Sleep seconds between requests")
    args = ap.parse_args()

    # Load accessions
    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            accs = normalize_accessions(fh.readlines())
    else:
        accs = normalize_accessions(args.accessions)

    if not accs:
        print("No accessions provided after normalization.", file=sys.stderr)
        sys.exit(1)

    # Prepare outputs
    tsv_fh = open(args.out_tsv, "w", newline="", encoding="utf-8")
    jsonl_fh = open(args.out_jsonl, "w", encoding="utf-8")
    tsv_w = csv.writer(tsv_fh, delimiter="\t")
    tsv_w.writerow(["input_accession", "metadata_json"])

    total_rows = 0
    for acc in accs:
        try:
            # 1) esearch: resolve to SRA UIDs (works for SRX or ERX; ERX is recognized by SRA Entrez)
            uids = esearch_sra_ids(acc, api_key=args.api_key, email=args.email)
            time.sleep(args.sleep)

            if not uids:
                # Write empty JSON for visibility
                payload = {"input_accession": acc, "note": "no SRA records found"}
                blob = json.dumps(payload, ensure_ascii=False)
                tsv_w.writerow([acc, blob])
                jsonl_fh.write(blob + "\n")
                total_rows += 1
                continue

            # 2) efetch XML and convert to JSON
            xml_text = efetch_sra_xml(uids, api_key=args.api_key, email=args.email)
            time.sleep(args.sleep)

            json_obj = xml_to_json_obj(xml_text)
            # Pack as a uniform record: keep original input, UIDs list, and full package(s)
            record = {
                "input_accession": acc,
                "sra_uids": uids,
                "experiment_package": json_obj,  # full metadata (EXPERIMENT_PACKAGE or list thereof)
            }
            blob = json.dumps(record, ensure_ascii=False)

            tsv_w.writerow([acc, blob])
            jsonl_fh.write(blob + "\n")
            total_rows += 1

        except requests.HTTPError as e:
            err = {"input_accession": acc, "error": f"HTTPError: {e}"}
            blob = json.dumps(err, ensure_ascii=False)
            tsv_w.writerow([acc, blob])
            jsonl_fh.write(blob + "\n")
        except Exception as e:
            err = {"input_accession": acc, "error": f"{type(e).__name__}: {e}"}
            blob = json.dumps(err, ensure_ascii=False)
            tsv_w.writerow([acc, blob])
            jsonl_fh.write(blob + "\n")

    tsv_fh.close()
    jsonl_fh.close()
    print(f"✅ Wrote {total_rows} rows to:\n  - {args.out_tsv}\n  - {args.out_jsonl}", file=sys.stderr)


if __name__ == "__main__":
    main()
