"""
Dataset Preparation Script
Generates synthetic document images for CNN Transfer Learning training.
"""
import os
import sys
import cv2
import numpy as np

# Reconfigure stdout to support emojis on Windows command prompt
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

CLASSES = ["Good Document", "Blurry Document", "Skewed Document", "Low Quality Scan", "Damaged Document"]
DATASET_DIR = "dataset/document_quality"

def main():
    print("=" * 50)
    print("DATASET PREPARATION FOR CNN TRAINING")
    print("=" * 50)
    
    for c in CLASSES:
        path = os.path.join(DATASET_DIR, c)
        os.makedirs(path, exist_ok=True)
        
        # Generate synthetic document images
        for i in range(10):
            img = np.ones((224, 224, 3), dtype=np.uint8) * 240 # Light grey paper background
            # Draw lines to simulate document text
            for y in range(30, 200, 25):
                cv2.line(img, (20, y), (np.random.randint(150, 200), y), (50, 50, 50), 2)
            cv2.putText(img, f"CLASS: {c.upper()}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(img, f"Doc ID: SP-{i:03d}", (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
            
            if "Blurry" in c:
                img = cv2.GaussianBlur(img, (15, 15), 0)
            elif "Low Quality" in c:
                img = cv2.resize(img, (48, 48))
                img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_NEAREST)
            elif "Skewed" in c:
                # Rotate image slightly
                center = (112, 112)
                M = cv2.getRotationMatrix2D(center, 12.0, 1.0)
                img = cv2.warpAffine(img, M, (224, 224), borderMode=cv2.BORDER_REPLICATE)
            elif "Damaged" in c:
                # Draw random black shapes/scratches
                cv2.circle(img, (112, 112), 40, (0, 0, 0), -1)
                cv2.line(img, (0, 0), (224, 224), (0, 0, 0), 4)
                
            cv2.imwrite(os.path.join(path, f"sample_{i}.jpg"), img)
            
        print(f"✅ Generated 10 synthetic samples for '{c}'")
        
    print("\nDataset generation complete.")
    print(f"Path: {os.path.abspath(DATASET_DIR)}")

if __name__ == "__main__":
    main()
