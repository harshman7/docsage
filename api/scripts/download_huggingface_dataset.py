"""
CLI script: Download Hugging Face invoice/receipt dataset and extract images.
"""
import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from PIL import Image
import argparse

def download_dataset(
    dataset_name: str = "mychen76/invoices-and-receipts_ocr_v1",
    output_dir: str = "data/raw_docs",
    split: str = "train",
    max_images: int = None,
    extract_ocr: bool = False
):
    """
    Download Hugging Face dataset and extract images.
    
    Args:
        dataset_name: Hugging Face dataset identifier
        output_dir: Directory to save images
        split: Dataset split to use (train, test, valid)
        max_images: Maximum number of images to download (None for all)
        extract_ocr: Whether to also extract OCR text to JSON files
    """
    print(f"📥 Downloading dataset: {dataset_name}")
    print(f"   Split: {split}")
    print(f"   Output: {output_dir}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset
        print("\n⏳ Loading dataset from Hugging Face...")
        dataset = load_dataset(dataset_name, split=split)
        
        print(f"✓ Dataset loaded: {len(dataset)} items")
        
        # Determine how many to process
        num_to_process = len(dataset) if max_images is None else min(max_images, len(dataset))
        print(f"📸 Processing {num_to_process} images...\n")
        
        # Process each item
        saved_count = 0
        skipped_count = 0
        
        for i, example in enumerate(dataset):
            if max_images and i >= max_images:
                break
            
            try:
                # Get the image
                if "image" in example:
                    image = example["image"]
                    
                    # Generate filename
                    filename = f"invoice_{split}_{i:04d}.png"
                    filepath = output_path / filename
                    
                    # Save image
                    if isinstance(image, Image.Image):
                        image.save(filepath, "PNG")
                    else:
                        # If it's not a PIL Image, try to convert
                        Image.fromarray(image).save(filepath, "PNG")
                    
                    saved_count += 1
                    
                    # Extract OCR data if requested
                    if extract_ocr:
                        ocr_data = {
                            "id": example.get("id", f"{split}_{i}"),
                            "raw_data": example.get("raw_data", ""),
                            "parsed_data": example.get("parsed_data", ""),
                        }
                        
                        # Save OCR data as JSON
                        import json
                        json_path = output_path / f"{filename}.json"
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(ocr_data, f, indent=2, ensure_ascii=False)
                    
                    if (i + 1) % 10 == 0:
                        print(f"   Processed {i + 1}/{num_to_process}...")
                        
            except Exception as e:
                print(f"   ⚠️  Error processing item {i}: {str(e)}")
                skipped_count += 1
                continue
        
        print(f"\n✓ Download complete!")
        print(f"   ✅ Saved: {saved_count} images")
        if skipped_count > 0:
            print(f"   ⚠️  Skipped: {skipped_count} images")
        print(f"   📁 Location: {output_path.absolute()}")
        
        if extract_ocr:
            print(f"   📄 OCR data: {saved_count} JSON files")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Review images in: {output_path}")
        print(f"   2. Ingest documents: python3 scripts/ingest_docs.py")
        print(f"   3. Build embeddings: python3 scripts/build_embeddings.py")
        
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {str(e)}")
        print(f"\n💡 Troubleshooting:")
        print(f"   - Make sure you have internet connection")
        print(f"   - Install required packages: pip install datasets pillow")
        print(f"   - Check dataset name is correct: {dataset_name}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description="Download Hugging Face invoice/receipt dataset"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="mychen76/invoices-and-receipts_ocr_v1",
        help="Hugging Face dataset name"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw_docs",
        help="Output directory for images"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "test", "valid"],
        help="Dataset split to download"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Maximum number of images to download (for testing)"
    )
    parser.add_argument(
        "--extract-ocr",
        action="store_true",
        help="Also extract OCR text data to JSON files"
    )
    
    args = parser.parse_args()
    
    download_dataset(
        dataset_name=args.dataset,
        output_dir=args.output,
        split=args.split,
        max_images=args.max_images,
        extract_ocr=args.extract_ocr
    )

if __name__ == "__main__":
    main()

