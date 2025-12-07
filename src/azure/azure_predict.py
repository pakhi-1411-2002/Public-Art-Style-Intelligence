import os
import time
import json
from pathlib import Path
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from msrest.authentication import ApiKeyCredentials
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")
TRAINING_KEY = os.getenv("AZURE_CV_TRAINING_KEY")
PROJECT_NAME = os.getenv("AZURE_CV_PROJECT_NAME", "PublicArtStyleClassifier")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def find_project(trainer):
    print(f" Looking for project: {PROJECT_NAME}")
    
    projects = trainer.get_projects()
    for proj in projects:
        if proj.name == PROJECT_NAME:
            print(f" Found project: {proj.id}")
            return proj
    
    print(f"\n Project '{PROJECT_NAME}' not found.")
    print("\n Available projects:")
    for proj in projects:
        print(f"  • {proj.name} (ID: {proj.id})")
    
    if projects:
        print(f"\n Update AZURE_CV_PROJECT_NAME in .env to match one above")
    
    return None

def get_project_stats(trainer, project):
    print("\n Project Statistics:")
    
    tags = trainer.get_tags(project.id)
    print(f"    Tags: {len(tags)}")
    
    images = trainer.get_tagged_images(project.id, take=1)
    total_images = images.total_tagged_images
    print(f"   Tagged images: {total_images}")
    
    print(f"\n   Tag distribution:")
    for tag in sorted(tags, key=lambda t: t.name):
        tag_images = trainer.get_tagged_images(
            project.id, 
            tag_ids=[tag.id],
            take=1
        )
        count = tag_images.total_tagged_images
        print(f"     • {tag.name}: {count} images")
    
    return {
        "tag_count": len(tags),
        "total_images": total_images,
        "tags": [{"name": tag.name, "id": tag.id} for tag in tags]
    }

def check_training_readiness(stats):
    print("\nTraining Readiness Check:")
    
    ready = True
    
    if stats["tag_count"] < 2:
        print("   Need at least 2 tags")
        ready = False
    else:
        print(f"   {stats['tag_count']} tags found")
    
    if stats["total_images"] < stats["tag_count"] * 5:
        print(f"    Minimum 5 images per tag recommended")
        print(f"     Current average: {stats['total_images'] / stats['tag_count']:.1f} images/tag")
    else:
        print(f"   {stats['total_images']} total images")
    
    return ready

def train_model(trainer, project):
    print("\n" + "=" * 60)
    print("Starting Training")
    print("=" * 60)
    print("\nThis typically takes 5-15 minutes...")
    print("   (Depends on dataset size and Azure load)")
    
    start_time = time.time()
    
    try:
        iteration = trainer.train_project(project.id)
        print(f"\nTraining initiated: Iteration {iteration.id}")
    except Exception as e:
        print(f"\nTraining failed to start: {e}")
        return None
    
    last_status = None
    while iteration.status not in ["Completed", "Failed"]:
        time.sleep(10)
        iteration = trainer.get_iteration(project.id, iteration.id)
        
        if iteration.status != last_status:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] Status: {iteration.status}")
            last_status = iteration.status
    
    elapsed = int(time.time() - start_time)
    
    if iteration.status == "Completed":
        print(f"\nTraining completed in {elapsed}s ({elapsed//60}m {elapsed%60}s)")
        return iteration
    else:
        print(f"\nTraining failed: {iteration.status}")
        return None

def evaluate_model(trainer, project, iteration):
    print("\n" + "=" * 60)
    print("Model Evaluation")
    print("=" * 60)
    
    performance = trainer.get_iteration_performance(project.id, iteration.id)
    
    metrics = {
        "iteration_id": iteration.id,
        "iteration_name": iteration.name,
        "created": iteration.created.isoformat(),
        "overall": {
            "precision": round(performance.precision, 4),
            "recall": round(performance.recall, 4),
            "average_precision": round(performance.average_precision, 4)
        },
        "per_tag_performance": []
    }
    
    print(f"\nOverall Performance:")
    print(f"  Precision:         {performance.precision:.1%}")
    print(f"  Recall:            {performance.recall:.1%}")
    print(f"  Average Precision: {performance.average_precision:.1%}")
    
    print(f"\nPer-Tag Performance:")
    print(f"  {'Tag':<25} {'Precision':<12} {'Recall':<12} {'AP':<12}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12}")
    
    sorted_tags = sorted(
        performance.per_tag_performance,
        key=lambda x: x.average_precision,
        reverse=True
    )
    
    for tag_perf in sorted_tags:
        print(f"  {tag_perf.name:<25} {tag_perf.precision:<12.1%} {tag_perf.recall:<12.1%} {tag_perf.average_precision:<12.1%}")
        
        metrics["per_tag_performance"].append({
            "tag": tag_perf.name,
            "precision": round(tag_perf.precision, 4),
            "recall": round(tag_perf.recall, 4),
            "average_precision": round(tag_perf.average_precision, 4)
        })
    
    return metrics

def publish_iteration(trainer, project, iteration):
    publish_name = f"{PROJECT_NAME}_v{iteration.name.replace('Iteration ', '')}"
    prediction_resource_id = os.getenv("AZURE_CV_PREDICTION_RESOURCE_ID")
    
    print("\n" + "=" * 60)
    print("Publishing Model")
    print("=" * 60)
    
    if not prediction_resource_id:
        print("\nAZURE_CV_PREDICTION_RESOURCE_ID not set in .env")
        print("   Get this from Azure Portal:")
        print("   Resource → Properties → Resource ID")
        print("\n   Skipping publish step (you can publish manually later)")
        return None
    
    print(f"\nPublishing as '{publish_name}'...")
    
    try:
        trainer.publish_iteration(
            project.id,
            iteration.id,
            publish_name,
            prediction_resource_id
        )
        print("Model published and ready for predictions!")
        return publish_name
    except Exception as e:
        print(f"Publish failed: {e}")
        return None

def save_outputs(project, iteration, publish_name, metrics, stats):
    
    config = {
        "project_id": project.id,
        "project_name": project.name,
        "iteration_id": iteration.id,
        "iteration_name": iteration.name,
        "published_name": publish_name,
        "endpoint": ENDPOINT,
        "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
        "domain": project.domain_id
    }
    
    config_path = OUTPUT_DIR / "azure_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nSaved config → {config_path}")
    
    metrics_path = OUTPUT_DIR / "azure_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics → {metrics_path}")
    
    report_path = OUTPUT_DIR / "training_report.txt"
    with open(report_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("Azure Custom Vision Training Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Project: {project.name}\n")
        f.write(f"Iteration: {iteration.name}\n")
        f.write(f"Date: {config['training_date']}\n\n")
        f.write(f"Dataset:\n")
        f.write(f"  • {stats['tag_count']} art styles\n")
        f.write(f"  • {stats['total_images']} total images\n\n")
        f.write(f"Overall Performance:\n")
        f.write(f"  • Precision: {metrics['overall']['precision']:.1%}\n")
        f.write(f"  • Recall: {metrics['overall']['recall']:.1%}\n")
        f.write(f"  • Average Precision: {metrics['overall']['average_precision']:.1%}\n\n")
        f.write(f"Status: {'Published' if publish_name else 'Not published'}\n")
    
    print(f"Saved report → {report_path}")

def main():
    print("=" * 60)
    print("Azure Custom Vision Training Pipeline")
    print("=" * 60)
    
    if not ENDPOINT or not TRAINING_KEY:
        print("\nError: Azure credentials not found in .env")
        print("Required: AZURE_CV_ENDPOINT and AZURE_CV_TRAINING_KEY")
        return
    
    print("\nConnecting to Azure Custom Vision...")
    credentials = ApiKeyCredentials(in_headers={"Training-key": TRAINING_KEY})
    trainer = CustomVisionTrainingClient(ENDPOINT, credentials)
    print("Connected")
    
    project = find_project(trainer)
    if not project:
        return
    
    stats = get_project_stats(trainer, project)
    
    if not check_training_readiness(stats):
        print("\nProject not ready for training")
        return
    
    print("\n" + "=" * 60)
    print("Ready to train!")
    print("=" * 60)
    response = input("\nStart training? [Y/n]: ").strip().lower()
    
    if response and response != 'y':
        print("Training cancelled")
        return
    
    iteration = train_model(trainer, project)
    if not iteration:
        return
    

    metrics = evaluate_model(trainer, project, iteration)
    

    publish_name = publish_iteration(trainer, project, iteration)
    

    save_outputs(project, iteration, publish_name, metrics, stats)
    

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()