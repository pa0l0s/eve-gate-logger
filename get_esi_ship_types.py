#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from pathlib import Path


ESI_BASE = "https://esi.evetech.net/latest"
DATASOURCE = "tranquility"
LANGUAGE = "en"


def curl_json(method, path, payload=None):
    url = f"{ESI_BASE}{path}"
    separator = "&" if "?" in url else "?"
    url = f"{url}{separator}datasource={DATASOURCE}&language={LANGUAGE}"

    cmd = ["curl", "-fsSL"]
    if method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(payload)])
    cmd.append(url)

    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"ESI request failed: {' '.join(cmd)}", file=sys.stderr)
        raise exc
    return json.loads(output)


def chunks(values, size):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def main():
    category = curl_json("GET", "/universe/categories/6/")
    if category.get("name") != "Ship":
        raise RuntimeError(f"Expected category 6 to be Ship, got {category!r}")

    rows = []
    type_ids = []

    for group_id in category["groups"]:
        group = curl_json("GET", f"/universe/groups/{group_id}/")
        if not group.get("published", False):
            continue

        for type_id in group.get("types", []):
            rows.append(
                {
                    "type_id": type_id,
                    "type_name": "",
                    "group_id": group["group_id"],
                    "group_name": group["name"],
                }
            )
            type_ids.append(type_id)

    names_by_id = {}
    for batch in chunks(type_ids, 1000):
        for item in curl_json("POST", "/universe/names/", batch):
            names_by_id[item["id"]] = item["name"]

    for row in rows:
        row["type_name"] = names_by_id.get(row["type_id"], "")

    rows.sort(key=lambda row: (row["group_name"].lower(), row["type_name"].lower(), row["type_id"]))

    out_dir = Path("esi_ship_types")
    out_dir.mkdir(exist_ok=True)

    csv_path = out_dir / "ship_types.csv"
    json_path = out_dir / "ship_types.json"

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["type_id", "type_name", "group_id", "group_name"])
        writer.writeheader()
        writer.writerows(rows)

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(rows, json_file, indent=2, ensure_ascii=False)
        json_file.write("\n")

    print(f"Wrote {len(rows)} ship types")
    print(csv_path)
    print(json_path)


if __name__ == "__main__":
    main()
