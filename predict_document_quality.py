"""
Document Quality Prediction Script
Inference pipeline using OpenCV and Deep Learning CNN.
"""
import sys
import os
from smartai.document_quality import analyze_document_quality
from smartai.computer_vision import detect_blur, detect_edges, enhance_contrast

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    print("=" * 60)
    print("SMARTPRINT AI - ACCELERATED INFERENCE PIPELINE")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        # Generate dataset if missing to ensure sample path works
        dataset_dir = "dataset/document_quality/Good Document"
        if not os.path.exists(dataset_dir):
            import prepare_dataset
            prepare_dataset.main()
        image_path = "dataset/document_quality/Good Document/sample_0.jpg"
        print(f"No image path specified. Using default: {image_path}")
    else:
        image_path = sys.argv[1]
        
    if not os.path.exists(image_path):
        print(f"❌ Error: Image path '{image_path}' does not exist.")
        sys.exit(1)
        
    print("\n[Step 1] OpenCV Preprocessing...")
    is_blurry, variance = detect_blur(image_path)
    print(f"   - Laplacian Variance: {variance:.2f}")
    if is_blurry:
        print("   - OpenCV Status: ⚠️ Blurred Document Detected!")
    else:
        print("   - OpenCV Status: ✅ Sharpness within acceptable thresholds.")
        
    # Test other OpenCV routines to ensure pipeline works
    os.makedirs('scratch', exist_ok=True)
    enhance_contrast(image_path, 'scratch/temp_contrast.jpg')
    detect_edges(image_path, 'scratch/temp_edges.jpg')
    print("   - Generated contrast-enhanced and edge-map intermediates in scratch/")
        
    print("\n[Step 2] Deep Learning CNN Inference (MobileNetV2)...")
    results = analyze_document_quality(image_path)
    
    print("\n" + "="*25 + " INFERENCE REPORT " + "="*25)
    print(f"Category:       {results['category']}")
    print(f"Quality Score:  {results['quality_score']}%")
    print(f"Confidence:     {results['confidence']*100:.1f}%")
    print(f"Recommendation: {results['recommendation']}")
    print(f"Model Pipeline: {results.get('model_type', 'N/A')}")
    print("Suggestions:")
    for s in results['suggestions']:
        print(f" - {s}")
    print("=" * 68)

if __name__ == "__main__":
    main()
