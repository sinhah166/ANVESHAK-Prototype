"""
ANVESHAK — Model Evaluation Utilities
Metrics computation, confusion matrix, and feature importance analysis.
"""

from typing import Any, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    class_names: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Compute comprehensive classification metrics.

    Returns:
        Dictionary with accuracy, precision, recall, F1, confusion matrix,
        per-class metrics, and ROC-AUC if probabilities provided.
    """
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }

    # Per-class report
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    metrics["per_class"] = {
        k: v for k, v in report.items()
        if k not in ("accuracy", "macro avg", "weighted avg")
    }

    if class_names:
        metrics["class_names"] = class_names

    # ROC-AUC if probabilities available
    if y_proba is not None:
        try:
            n_classes = y_proba.shape[1] if len(y_proba.shape) > 1 else 1
            if n_classes > 1:
                metrics["roc_auc_ovr"] = float(
                    roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro")
                )
        except Exception:
            pass

    return metrics


def compute_feature_importance(
    model,
    feature_names: list[str],
) -> dict[str, float]:
    """
    Extract feature importances from a fitted model.

    Supports RandomForest, GradientBoosting (feature_importances_)
    and LogisticRegression (coef_).
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_).mean(axis=0)
    else:
        return {}

    return {
        name: float(imp)
        for name, imp in sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )
    }
