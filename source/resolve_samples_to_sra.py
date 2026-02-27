
#!/usr/bin/env python3
"""
Resolve SAMEA/ERS/SAMN/SRS sample accessions to SRA Experiments (SRX) and Runs (SRR)
using NCBI Entrez E-utilities (esearch + efetch). Optionally produce a naive SRX->ERX map.

Usage examples:
  python resolve_samples_to_sra.py --input samples.txt --api-key YOUR_NCBI_KEY --out sra_map.tsv
  python resolve_samples_to_sra.py --accessions ERS21180437 ERS8291035 --out sra_map.tsv --map-erx

Notes:
- E-utilities reference and parameters: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/  (esearch, efetch)  [documented]
- SRA hierarchy/prefixes (SRX, SRR, SRS) and ENA (ERX, ERR, ERS) are INSDC equivalents. Verify ERX in ENA if needed.

"""

import argparse
import csv
import os
import sys
import time
import typing as t
import xml.etree.ElementTree as ET

import requests

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ESERACH_URL = f"{EUTILS_BASE}/esearch.fcgi"
EFETCH_URL = f"{EUTILS_BASE}/efetch.fcgi"

# Conservative rate limit: ~3 requests/sec (NCBI guidance; increase if needed with API key)
DEFAULT_SLEEP = 0.4


def esearch_sra_for_accession(term: str, api_key: t.Optional[str] = None, email: t.Optional[str] = None) -> t.List[str]:
    """
    Query NCBI E-utilities esearch for SRA IDs matching the accession term.
    Returns a list of UIDs (SRA record IDs).
    """
    params = {
        "db": "sra",
        "term": term,          # accession or query string
        "retmode": "json",
        "retmax": "10000",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    r = requests.get(ESERACH_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    ids = data.get("esearchresult", {}).get("idlist", [])
    return ids


def efetch_sra_xml(ids: t.List[str], api_key: t.Optional[str] = None, email: t.Optional[str] = None) -> str:
    """
    Fetch SRA XML for a list of UIDs via efetch.
    """
    if not ids:
        return ""
    params = {
        "db": "sra",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    r = requests.get(EFETCH_URL, params=params, timeout=90)
    r.raise_for_status()
    return r.text


def parse_sra_xml(xml_text: str) -> t.List[dict]:
    """
    Parse SRA XML and extract SRS (sample), SRX (experiment), and SRR (runs).
    Returns a list of dicts with keys: srs, srx, srr_list
    """
    if not xml_text.strip():
        return []

    # The XML typically has EXPERIMENT_PACKAGE_SET or multiple EXPERIMENT_PACKAGE entries
    # Structure:
    # <EXPERIMENT_PACKAGE>
    #   <SAMPLE accession="SRS...">...</SAMPLE>
    #   <EXPERIMENT accession="SRX...">...</EXPERIMENT>
    #   <RUN_SET><RUN accession="SRR...">...</RUN>...</RUN_SET>
    # </EXPERIMENT_PACKAGE>
    results = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return results

    # Support both 'EXPERIMENT_PACKAGE' and 'EXPERIMENT_PACKAGE_SET'
    packages = []
    if root.tag.endswith("EXPERIMENT_PACKAGE_SET"):
        packages = [child for child in root if child.tag.endswith("EXPERIMENT_PACKAGE")]
    elif root.tag.endswith("EXPERIMENT_PACKAGE"):
        packages = [root]
    else:
        # Try to find any EXPERIMENT_PACKAGE elements
        packages = root.findall(".//EXPERIMENT_PACKAGE")

    for pkg in packages:
        srs = None
        srx = None
        srrs: t.List[str] = []

        # SAMPLE accession
        sample_el = pkg.find(".//SAMPLE")
        if sample_el is not None:
            srs = sample_el.get("accession")

        # EXPERIMENT accession
        exp_el = pkg.find(".//EXPERIMENT")
        if exp_el is not None:
            srx = exp_el.get("accession")

        # RUNs
        run_set = pkg.find(".//RUN_SET")
        if run_set is not None:
            for run in run_set.findall(".//RUN"):
                acc = run.get("accession")
                if acc:
                    srrs.append(acc)

        # Only add if we have at least an SRX or SRR
        if srx or srrs or srs:
            results.append({"srs": srs, "srx": srx, "srr_list": srrs})

    return results


def normalize_inputs(lines: t.List[str]) -> t.List[str]:
    cleaned = []
    for ln in lines:
        ln = ln.strip().replace("\r", "")
        if not ln:
            continue
        cleaned.append(ln)
    # Unique order-preserving
    seen = set()
    uniq = []
    for a in cleaned:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def main():
    ap = argparse.ArgumentParser(
        description="Resolve SAMEA/ERS/SAMN/SRS sample accessions to SRA SRX/SRR via NCBI E-utilities; optionally map SRX->ERX."
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="Text file with one accession per line")
    g.add_argument("--accessions", nargs="+", help="Accessions provided on the command line (ERS/SAMEA/SAMN/SRS)")
    ap.add_argument("--out", default="SRA_sample_to_SRX_SRR.tsv", help="Output TSV path")
    ap.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"), help="NCBI API key (env NCBI_API_KEY is used if set)")
    ap.add_argument("--email", default=os.environ.get("EMAIL"), help="Contact email (optional but recommended by NCBI)")
    ap.add_argument("--sleep", type=float, default=DEFAULT_SLEEP, help="Seconds to sleep between requests (rate limiting)")
    ap.add_argument("--map-erx", action="store_true", help="Also write naive SRX->ERX mapping TSV")
    args = ap.parse_args()

    # Load accessions
    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            accs = normalize_inputs(fh.readlines())
    else:
        accs = normalize_inputs(args.accessions)

    # Prepare output TSV
    out_fh = open(args.out, "w", newline="", encoding="utf-8")
    w = csv.writer(out_fh, delimiter="\t")
    w.writerow(["input_accession", "sra_sample_accession", "sra_experiment_accession", "sra_run_accession"])

    total_rows = 0
    all_srx = set()

    for acc in accs:
        try:
            # First: esearch SRA by accession (supports ERS/SAMEA/SAMN/SRS too)
            ids = esearch_sra_for_accession(acc, api_key=args.api_key, email=args.email)
            time.sleep(args.sleep)

            if not ids:
                # No SRA records found; write a placeholder line
                w.writerow([acc, "", "", ""])
                continue

            # Then: efetch XML and parse SRX/SRR/SRS
            xml_text = efetch_sra_xml(ids, api_key=args.api_key, email=args.email)
            time.sleep(args.sleep)

            pkgs = parse_sra_xml(xml_text)
            if not pkgs:
                w.writerow([acc, "", "", ""])
                continue

            for pkg in pkgs:
                srs = pkg.get("srs") or ""
                srx = pkg.get("srx") or ""
                if srx:
                    all_srx.add(srx)
                srrs = pkg.get("srr_list") or []
                if srrs:
                    for srr in srrs:
                        w.writerow([acc, srs, srx, srr])
                        total_rows += 1
                else:
                    # At least write the SRX/SRS even if no SRR
                    w.writerow([acc, srs, srx, ""])
                    total_rows += 1

        except requests.HTTPError as e:
            print(f"[HTTPError] accession={acc}: {e}", file=sys.stderr)
            w.writerow([acc, "", "", ""])
        except Exception as e:
            print(f"[Error] accession={acc}: {e}", file=sys.stderr)
            w.writerow([acc, "", "", ""])

    out_fh.close()
    print(f"Wrote {total_rows} rows to {args.out}", file=sys.stderr)

    # Optional SRX -> ERX map (naive prefix swap)
    if args.map_erx and all_srx:
        erx_map_path = os.path.splitext(args.out)[0] + "_SRX_to_ERX.tsv"
        with open(erx_map_path, "w", newline="", encoding="utf-8") as fh:
            w2 = csv.writer(fh, delimiter="\t")
            w2.writerow(["sra_experiment_accession(SRX)", "ena_experiment_accession(ERX)"])
            for srx in sorted(all_srx):
                erx = srx.replace("SRX", "ERX", 1)  # INSDC-equivalent accession in ENA
                w2.writerow([srx, erx])
        print(f"Wrote SRX->ERX map to {erx_map_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
