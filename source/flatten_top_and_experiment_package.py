
#!/usr/bin/env python3
"""
Flatten a TSV with a JSON column:
 - Add one column per top-level key in the JSON blob.
 - Un-nest 'experiment_package' exactly one level and add prefixed columns.

Usage:
  python flatten_top_and_experiment_package.py \
      --input sra_experiment_metadata.tsv \
      --out flatten_top_plus_one.tsv \
      --json-col metadata_json \
      --package-mode first \
      --package-prefix experiment_package__ \
      --fill-na ""

Options:
  --package-mode {first,concat}
    - first  : if experiment_package is a list, flatten only the first item
    - concat : if experiment_package is a list, collect values from all items per immediate key,
               and store as JSON array (string) in the prefixed column

  --fill-na TEXT
    - value to fill for missing cells (default empty string "")
"""

import argparse
import json
import sys
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


def parse_json_safe(s: Any) -> Optional[Any]:
    """Return parsed JSON if possible, else None."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    if isinstance(s, (dict, list)):
        return s  # already parsed
    try:
        return json.loads(str(s))
    except Exception:
        return None


def compact_json(v: Any) -> str:
    """Serialize dict/list to a compact JSON string; scalars returned as-is string."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, separators=(",", ":"))
    return "" if v is None else str(v)


def flatten_top_level(obj: Any) -> Dict[str, Any]:
    """
    Flatten only top-level keys of a JSON object:
      - scalars kept as-is
      - dict/list re-serialized to compact JSON strings
    """
    out: Dict[str, Any] = {}
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        if isinstance(v, (dict, list)):
            out[k] = compact_json(v)
        else:
            out[k] = v
    return out


def flatten_experiment_package_one_level(
    obj: Any,
    mode: str = "first",
    prefix: str = "experiment_package__",
) -> Dict[str, Any]:
    """
    Un-nest 'experiment_package' exactly one level into prefixed columns.

    Cases:
      - obj is dict: flatten immediate keys under 'experiment_package'
      - obj is list: depends on mode:
          * first: flatten immediate keys of the FIRST item only
          * concat: per immediate key, collect values across all items -> JSON array string
    Deeper children (dict/list values of immediate keys) are compact JSON strings.
    """
    out: Dict[str, Any] = {}

    # If obj is a string that represents JSON, parse it
    obj = parse_json_safe(obj)

    if isinstance(obj, dict):
        for k, v in obj.items():
            col = f"{prefix}{k}"
            out[col] = compact_json(v)

    elif isinstance(obj, list) and obj:
        if mode == "first":
            first = obj[0]
            if isinstance(first, dict):
                for k, v in first.items():
                    col = f"{prefix}{k}"
                    out[col] = compact_json(v)
            else:
                # Non-dict first element; store entire first as JSON
                out[prefix.rstrip("_")] = compact_json(first)

        elif mode == "concat":
            # Collect values per immediate key across all dict items
            bucket: Dict[str, List[Any]] = {}
            for item in obj:
                if isinstance(item, dict):
                    for k, v in item.items():
                        bucket.setdefault(k, []).append(v)
                else:
                    # Non-dict item; bucket under a generic key
                    bucket.setdefault("_items", []).append(item)

            for k, vals in bucket.items():
                col = f"{prefix}{k}"
                # For concat, always store as JSON array (compact)
                compact_vals = []
                for v in vals:
                    # keep structure; compact later
                    compact_vals.append(v)
                out[col] = json.dumps(compact_vals, separators=(",", ":"))

        else:
            # Unknown mode; no-op
            pass

    else:
        # obj is None or scalar; nothing to flatten
        pass

    return out


def main():
    ap = argparse.ArgumentParser(description="Flatten top-level JSON keys and un-nest experiment_package one level.")
    ap.add_argument("--input", required=True, help="Input TSV file with a JSON column")
    ap.add_argument("--out", required=True, help="Output TSV file")
    ap.add_argument("--json-col", default="metadata_json", help="Name of the JSON column (default: metadata_json)")
    ap.add_argument("--package-mode", choices=["first", "concat"], default="first",
                    help="How to handle experiment_package lists (default: first)")
    ap.add_argument("--package-prefix", default="experiment_package__",
                    help="Prefix for flattened experiment_package columns (default: experiment_package__)")
    ap.add_argument("--fill-na", default="", help="Value to fill for missing cells (default: empty string)")
    args = ap.parse_args()

    try:
        # Read as strings to avoid pandas trying to infer types incorrectly
        df = pd.read_csv(args.input, sep="\t", dtype=str)
    except Exception as e:
        print(f"[ERROR] Could not read input TSV: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json_col not in df.columns:
        print(f"[ERROR] JSON column '{args.json_col}' not found in {args.input}", file=sys.stderr)
        sys.exit(1)

    # Flatten each row's JSON blob (top-level only), and un-nest experiment_package one level
    flat_rows: List[Dict[str, Any]] = []
    for blob in df[args.json_col]:
        parsed = parse_json_safe(blob)
        top = flatten_top_level(parsed)

        # Try to access experiment_package from the *parsed* object,
        # but also handle the case where top-level flattening stored it as a string.
        ep_value = None
        if isinstance(parsed, dict) and "experiment_package" in parsed:
            ep_value = parsed["experiment_package"]
        else:
            # if top has experiment_package as compact JSON string, parse it
            maybe = top.get("experiment_package", None)
            ep_value = parse_json_safe(maybe)

        ep_flat = flatten_experiment_package_one_level(
            ep_value, mode=args.package_mode, prefix=args.package_prefix
        )

        # Merge: top-level flattened + one-level experiment_package flattened
        row_flat = {**top, **ep_flat}
        flat_rows.append(row_flat)

    # Build meta DataFrame from the union of keys and fill missing values
    meta_df = pd.DataFrame(flat_rows).fillna(args.fill_na)

    # Keep all original columns except the JSON blob column
    non_json_cols = [c for c in df.columns if c != args.json_col]
    final_df = pd.concat([df[non_json_cols], meta_df], axis=1)

    # Write output
    try:
        final_df.to_csv(args.out, sep="\t", index=False)
        print(f"✅ Wrote flattened table to: {args.out}")
    except Exception as e:
        print(f"[ERROR] Could not write output TSV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
