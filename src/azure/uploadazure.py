import os
import glob
import time
from tqdm import tqdm

from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry, ImageFileCreateBatch
from msrest.authentication import ApiKeyCredentials


AZURE_ENDPOINT = "endpoint"
TRAINING_KEY = "training_key"
PROJECT_ID = "project_id"

DATASET_DIR = "data/raw/"
BATCH_SIZE = 50              # Azure allows max 64
RETRY_SLEEP = 2              # seconds to sleep when rate-limited


def upload_batch(trainer, batch, project_id):
    """Upload a batch with retry logic for rate-limits."""
    while True:
        try:
            result = trainer.create_images_from_files(project_id, batch)
            return result
        except Exception as e:
            if "Too Many Requests" in str(e):
                print("⚠️  Rate limit hit — sleeping and retrying...")
                time.sleep(RETRY_SLEEP)
            else:
                raise e


def main():
    credentials = ApiKeyCredentials(in_headers={"Training-key": TRAINING_KEY})
    trainer = CustomVisionTrainingClient(AZURE_ENDPOINT, credentials)

    # Get existing tags
    existing_tags = {t.name: t.id for t in trainer.get_tags(PROJECT_ID)}

    # Create tags if missing
    class_to_tag = {}
    for class_name in os.listdir(DATASET_DIR):
        class_path = os.path.join(DATASET_DIR, class_name)
        if not os.path.isdir(class_path):
            continue

        if class_name in existing_tags:
            class_to_tag[class_name] = existing_tags[class_name]
        else:
            tag = trainer.create_tag(PROJECT_ID, class_name)
            class_to_tag[class_name] = tag.id
            print(f"Created tag: {class_name}")

    # Upload images in batches
    for class_name, tag_id in class_to_tag.items():
        class_path = os.path.join(DATASET_DIR, class_name)

        file_paths = glob.glob(os.path.join(class_path, "**", "*.jpg"), recursive=True)
        file_paths += glob.glob(os.path.join(class_path, "**", "*.jpeg"), recursive=True)
        file_paths += glob.glob(os.path.join(class_path, "**", "*.png"), recursive=True)

        print(f"\nUploading {class_name}: {len(file_paths)} images")

        batch_entries = []
        for file_path in tqdm(file_paths, desc=f"Preparing {class_name}"):
            with open(file_path, "rb") as f:
                entry = ImageFileCreateEntry(
                    name=os.path.basename(file_path),
                    contents=f.read(),
                    tag_ids=[tag_id]
                )
                batch_entries.append(entry)

            # Send batch to Azure
            if len(batch_entries) == BATCH_SIZE:
                batch = ImageFileCreateBatch(images=batch_entries)
                upload_batch(trainer, batch, PROJECT_ID)
                batch_entries = []

        # Upload remaining images
        if batch_entries:
            batch = ImageFileCreateBatch(images=batch_entries)
            upload_batch(trainer, batch, PROJECT_ID)

    print("\n🎉 ALL IMAGES SUCCESSFULLY UPLOADED WITH BATCHING & RETRY LOGIC!")


if __name__ == "__main__":
    main()
