"""Build metadata from the downloaded Hugging Face image dataset."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "vision" / "jewelry-design-dataset" / "dataset"
OUTPUT = ROOT / "data" / "vision" / "image_metadata.csv"
SOURCE_URL = "https://huggingface.co/datasets/sidd707/jewelry-design-dataset"


def main() -> None:
    labels = DATASET / "dataset_labels.csv"
    rows = []
    with labels.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            image_path = row["image_path"].replace("\\", "/")
            category = image_path.split("/", 1)[0]
            rows.append({"image_id": f"HF-JEWELRY-{index:04d}", "category": category, "license": "MIT", "dataset_name": "sidd707/jewelry-design-dataset", "image_path": image_path, "description": row.get("description", ""), "source_url": SOURCE_URL, "data_kind": "external_reference", "is_external_reference": "true"})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Indexed {len(rows)} real dataset images.")


if __name__ == "__main__":
    main()
