import os
import glob
import json
from PIL import Image
from tqdm import tqdm

DATASET_DIR = "data/raw/"
OUTPUT_SUMMARY = "data/dataset_summary.json"


def is_corrupt(file_path):
    try:
        img = Image.open(file_path)
        img.verify()  
        return False
    except Exception:
        return True


def main():
    summary = {
        "total_images": 0,
        "classes": {},
        "corrupt_images": []
    }

    print(f"\nScanning dataset at: {DATASET_DIR}")

    if not os.path.exists(DATASET_DIR):
        print("ERROR: DATASET_DIR does not exist. Check folder path.")
        return

    class_folders = [f for f in os.listdir(DATASET_DIR)
                     if os.path.isdir(os.path.join(DATASET_DIR, f))]

    if not class_folders:
        print("ERROR: No class folders found inside data/raw/.")
        return

    print("\nFound class folders:", class_folders)

    for class_name in class_folders:
        class_path = os.path.join(DATASET_DIR, class_name)

        image_paths = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            image_paths.extend(glob.glob(os.path.join(class_path, "**", ext), recursive=True))

        print(f"\nClass '{class_name}': {len(image_paths)} images found")

        corrupt_count = 0

        for img_path in tqdm(image_paths, desc=f"Checking {class_name}"):
            if is_corrupt(img_path):
                summary["corrupt_images"].append(img_path)
                corrupt_count += 1

        summary["classes"][class_name] = {
            "total_images": len(image_paths),
            "corrupt_images": corrupt_count
        }

        summary["total_images"] += len(image_paths)

    os.makedirs(os.path.dirname(OUTPUT_SUMMARY), exist_ok=True)
    with open(OUTPUT_SUMMARY, "w") as f:
        json.dump(summary, f, indent=4)

    print("\n Dataset check complete!")
    print(f"Summary saved to: {OUTPUT_SUMMARY}")
    print(f"Total images: {summary['total_images']}")
    print(f"Corrupt images detected: {len(summary['corrupt_images'])}")


if __name__ == "__main__":
    main()
