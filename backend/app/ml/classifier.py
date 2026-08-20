"""
ANVESHAK — Exoplanet Candidate Classifier
scikit-learn based classification using RandomForestClassifier.

Target classes from KOI data:
- CONFIRMED
- CANDIDATE
- FALSE POSITIVE

Scientific disclaimer: This classifier provides model predictions based on
observed parameters. It does NOT confirm or deny the existence of exoplanets.
"""

import json
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from app.core.config import ML_ARTIFACTS_DIR
from app.core.logging import get_logger

logger = get_logger("ml.classifier")

# Default features for classification
CLASSIFICATION_FEATURES = [
    "orbital_period_days",
    "planet_radius_earth",
    "transit_depth",
    "transit_duration_hrs",
    "equilibrium_temp_k",
    "effective_temp_k",
    "stellar_radius_solar",
    "stellar_mass_solar",
    "surface_gravity_log_cgs",
    "model_snr",
    "impact_parameter",
    "eccentricity",
    "insolation_flux",
]


class ExoplanetClassifier:
    """
    Trains and runs classification models on exoplanet candidate data.

    Primary model: RandomForestClassifier
    Handles class imbalance via class_weight='balanced'.
    """

    ALGORITHMS = {
        "random_forest": lambda: RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "gradient_boosting": lambda: GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        ),
        "logistic_regression": lambda: LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
            multi_class="multinomial",
        ),
    }

    def __init__(self):
        self.model = None
        self.pipeline = None
        self.label_encoder = LabelEncoder()
        self.feature_names = CLASSIFICATION_FEATURES
        self.metrics = {}
        self.feature_importances = {}
        self.confusion_mat = None
        self.class_names = []

    def train(
        self,
        df: pd.DataFrame,
        label_column: str = "disposition",
        algorithm: str = "random_forest",
        feature_names: Optional[list[str]] = None,
        test_size: float = 0.2,
    ) -> dict[str, Any]:
        """
        Train a classification model.

        Args:
            df: DataFrame with features and label column.
            label_column: Name of the target label column.
            algorithm: Algorithm to use ('random_forest', 'gradient_boosting', 'logistic_regression').
            feature_names: Feature columns to use. None for defaults.
            test_size: Fraction for test split.

        Returns:
            Dictionary with training results and metrics.
        """
        if feature_names:
            self.feature_names = feature_names

        # Filter to available features
        available_features = [f for f in self.feature_names if f in df.columns]
        if len(available_features) < 3:
            raise ValueError(f"Insufficient features. Available: {available_features}")

        self.feature_names = available_features
        logger.info("training_classifier", algorithm=algorithm, features=len(available_features))

        # Prepare data
        X = df[available_features].copy()
        y = df[label_column].copy()

        # Drop rows where label is missing
        mask = y.notna()
        X = X[mask]
        y = y[mask]

        # Standardize labels
        y = y.str.upper().str.strip()
        # Map common label variations
        label_map = {
            "CONFIRMED": "CONFIRMED",
            "CANDIDATE": "CANDIDATE",
            "FALSE POSITIVE": "FALSE POSITIVE",
            "NOT DISPOSITIONED": "CANDIDATE",
        }
        y = y.map(lambda x: label_map.get(x, x))

        # Remove classes with too few samples
        class_counts = y.value_counts()
        valid_classes = class_counts[class_counts >= 5].index
        mask = y.isin(valid_classes)
        X = X[mask]
        y = y[mask]

        if len(X) < 20:
            raise ValueError(f"Insufficient training data: {len(X)} rows")

        # Encode labels
        self.label_encoder.fit(y)
        y_encoded = self.label_encoder.transform(y)
        self.class_names = list(self.label_encoder.classes_)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded,
        )

        # Build pipeline
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}. Available: {list(self.ALGORITHMS.keys())}")

        self.model = self.ALGORITHMS[algorithm]()
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", self.model),
        ])

        # Train
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        y_proba = None
        if hasattr(self.pipeline, "predict_proba"):
            try:
                y_proba = self.pipeline.predict_proba(X_test)
            except Exception:
                pass

        self.metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
            "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "n_classes": len(self.class_names),
            "class_names": self.class_names,
            "class_distribution": {name: int(count) for name, count in zip(*np.unique(y_encoded, return_counts=True))},
        }

        # ROC-AUC (multiclass)
        if y_proba is not None and len(self.class_names) > 1:
            try:
                self.metrics["roc_auc_ovr"] = float(
                    roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
                )
            except Exception:
                pass

        # Confusion matrix
        self.confusion_mat = confusion_matrix(y_test, y_pred).tolist()
        self.metrics["confusion_matrix"] = self.confusion_mat

        # Feature importance
        classifier = self.pipeline.named_steps["classifier"]
        if hasattr(classifier, "feature_importances_"):
            self.feature_importances = {
                name: float(imp)
                for name, imp in zip(self.feature_names, classifier.feature_importances_)
            }
            self.metrics["feature_importances"] = self.feature_importances

        logger.info(
            "training_complete",
            accuracy=self.metrics["accuracy"],
            f1=self.metrics["f1_macro"],
        )

        return self.metrics

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate predictions for new data.

        Returns DataFrame with predicted_class, confidence, and per-class probabilities.
        """
        if self.pipeline is None:
            raise RuntimeError("Model not trained. Call train() first.")

        available = [f for f in self.feature_names if f in df.columns]
        X = df[available].copy()

        # Add missing feature columns as NaN
        for f in self.feature_names:
            if f not in X.columns:
                X[f] = np.nan

        X = X[self.feature_names]

        predictions = self.pipeline.predict(X)
        pred_labels = self.label_encoder.inverse_transform(predictions)

        result = pd.DataFrame({"predicted_class": pred_labels})

        if hasattr(self.pipeline, "predict_proba"):
            try:
                probas = self.pipeline.predict_proba(X)
                result["confidence"] = probas.max(axis=1)
                for i, class_name in enumerate(self.class_names):
                    result[f"prob_{class_name}"] = probas[:, i]
            except Exception:
                result["confidence"] = 0.5

        return result

    def save(self, path: Optional[str] = None, version: str = "v1") -> str:
        """Save the trained model to disk."""
        if self.pipeline is None:
            raise RuntimeError("No trained model to save.")

        save_dir = Path(path) if path else ML_ARTIFACTS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        model_path = save_dir / f"classifier_{version}.joblib"
        meta_path = save_dir / f"classifier_{version}_meta.json"

        joblib.dump({
            "pipeline": self.pipeline,
            "label_encoder": self.label_encoder,
            "feature_names": self.feature_names,
            "class_names": self.class_names,
        }, model_path)

        with open(meta_path, "w") as f:
            json.dump({
                "version": version,
                "features": self.feature_names,
                "classes": self.class_names,
                "metrics": self.metrics,
            }, f, indent=2, default=str)

        logger.info("model_saved", path=str(model_path))
        return str(model_path)

    def load(self, path: Optional[str] = None, version: str = "v1") -> bool:
        """Load a trained model from disk."""
        load_dir = Path(path) if path else ML_ARTIFACTS_DIR
        model_path = load_dir / f"classifier_{version}.joblib"

        if not model_path.exists():
            logger.warning("model_not_found", path=str(model_path))
            return False

        data = joblib.load(model_path)
        self.pipeline = data["pipeline"]
        self.label_encoder = data["label_encoder"]
        self.feature_names = data["feature_names"]
        self.class_names = data["class_names"]
        self.model = self.pipeline.named_steps.get("classifier")

        # Load metrics if available
        meta_path = load_dir / f"classifier_{version}_meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
                self.metrics = meta.get("metrics", {})

        logger.info("model_loaded", path=str(model_path))
        return True
