"""
Transfer Learning Training Script
Trains a MobileNetV2 CNN for document quality classification and wait-time regressors.
"""
import os
import time
import sys

# Suppress TF logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image_dataset_from_directory
    from smartai.document_quality import build_document_classifier, CLASSES
    from smartai.wait_time import train_wait_time_models, ML_AVAILABLE
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

def train_cnn_model(epochs: int = 3) -> tuple[float, float, float]:
    """Train the CNN classification model on the synthetic document quality dataset."""
    if not TF_AVAILABLE:
        return 0.0, 0.0, 0.0
        
    dataset_dir = "dataset/document_quality"
    
    # 1. Trigger dataset preparation if it doesn't exist
    if not os.path.exists(dataset_dir) or len(os.listdir(dataset_dir)) < len(CLASSES):
        print("Dataset not found. Generating synthetic samples first...")
        import prepare_dataset
        prepare_dataset.main()
        
    start_time = time.time()
    
    # 2. Load dataset
    train_ds = image_dataset_from_directory(
        dataset_dir,
        labels='inferred',
        label_mode='categorical',
        batch_size=8,
        image_size=(224, 224),
        shuffle=True,
        seed=42,
        validation_split=0.2,
        subset='training',
        verbose=False
    )
    
    val_ds = image_dataset_from_directory(
        dataset_dir,
        labels='inferred',
        label_mode='categorical',
        batch_size=8,
        image_size=(224, 224),
        shuffle=True,
        seed=42,
        validation_split=0.2,
        subset='validation',
        verbose=False
    )
    
    # 3. Build model
    model = build_document_classifier()
    if model is None:
        print("Failed to build model.")
        return 0.0, 0.0, 0.0
        
    # 4. Fit model
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        verbose=1
    )
    
    # 5. Save model
    os.makedirs('models', exist_ok=True)
    model.save('models/document_quality_model.h5')
    
    training_time = time.time() - start_time
    final_accuracy = float(history.history['accuracy'][-1])
    final_loss = float(history.history['loss'][-1])
    
    return training_time, final_accuracy, final_loss

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    print("=" * 60)
    print("SMARTPRINT AI - RETRAINING PIPELINE")
    print("=" * 60)
    
    if not TF_AVAILABLE:
        print("❌ TensorFlow is not installed. Run: pip install tensorflow")
        sys.exit(1)
        
    epochs = 3
    if len(sys.argv) > 1:
        try:
            epochs = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"\n🧠 1. Starting Deep Learning CNN Transfer Learning (MobileNetV2)...")
    print(f"   Target Epochs: {epochs}")
    cnn_time, cnn_acc, cnn_loss = train_cnn_model(epochs=epochs)
    
    print("\n✅ CNN training complete!")
    print(f"   Saved weights to: models/document_quality_model.h5")
    print(f"   Training Time: {cnn_time:.2f} seconds")
    print(f"   Accuracy:      {cnn_acc*100:.1f}%")
    print(f"   Loss:          {cnn_loss:.4f}")
    
    print(f"\n📈 2. Starting Wait Time Predictor Training (Random Forest & XGBoost)...")
    if ML_AVAILABLE:
        start_ml = time.time()
        success = train_wait_time_models()
        ml_time = time.time() - start_ml
        if success:
            print("✅ Random Forest & XGBoost regressors trained successfully!")
            print("   Saved models/wait_time_rf.joblib")
            print("   Saved models/wait_time_xgb.json")
            print(f"   Regression Training Time: {ml_time:.2f} seconds")
        else:
            print("❌ Wait time training failed.")
    else:
        print("❌ Scikit-Learn or XGBoost not available. Skipping.")
        
    print("\n" + "=" * 60)
    print("ALL MODEL RETRAINING OPERATIONS COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()
