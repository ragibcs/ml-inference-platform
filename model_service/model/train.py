"""
Model Training and Serialization Script.

Trains a production-ready RandomForestClassifier on the standard 4-feature Iris dataset
and saves the serialized model pipeline artifact to disk.
"""

import os
import sys
import logging
from pathlib import Path
import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("model_trainer")


def train_and_save_model(
    output_path: str = "model_service/model/model.joblib",
    model_version: str = "v1.0.0",
    random_state: int = 42,
) -> Path:
    """Train classification model and save serialized artifact with metadata."""
    logger.info("Loading dataset for model training...")
    iris = load_iris()
    x_data = iris.data
    y_data = iris.target
    feature_names = iris.feature_names
    target_names = list(iris.target_names)

    logger.info(f"Dataset shape: {x_data.shape}, Target classes: {target_names}")

    x_train, x_test, y_train, y_test = train_test_split(
        x_data, y_data, test_size=0.2, random_state=random_state, stratify=y_data
    )

    logger.info("Building model pipeline (StandardScaler + RandomForestClassifier)...")
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=4,
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    logger.info("Fitting model...")
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info(f"Classification Report:\n{classification_report(y_test, y_pred, target_names=target_names)}")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "pipeline": pipeline,
        "model_version": model_version,
        "feature_names": feature_names,
        "expected_features_count": len(feature_names),
        "target_names": target_names,
        "metrics": {
            "test_accuracy": float(accuracy),
        },
    }

    joblib.dump(artifact, out_file)
    logger.info(f"Successfully exported model artifact to {out_file.resolve()}")
    return out_file


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "model_service/model/model.joblib"
    train_and_save_model(output_path=out)
