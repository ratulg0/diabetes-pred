from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary_classifier(y_true: Any, probabilities: np.ndarray, threshold: float = 0.5) -> dict[str, float | int]:
    predicted = (probabilities >= threshold).astype(int)
    true_negative, false_positive, false_negative, true_positive = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    specificity = true_negative / (true_negative + false_positive) if true_negative + false_positive else 0.0
    return {
        "accuracy": round(float(accuracy_score(y_true, predicted)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 6),
        "precision": round(float(precision_score(y_true, predicted, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, predicted, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, predicted, zero_division=0)), 6),
        "specificity": round(float(specificity), 6),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 6),
        "threshold": threshold,
        "true_negative": int(true_negative),
        "false_positive": int(false_positive),
        "false_negative": int(false_negative),
        "true_positive": int(true_positive),
    }
