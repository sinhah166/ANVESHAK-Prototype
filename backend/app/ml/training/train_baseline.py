"""
ANVESHAK — Baseline Classifier Training Script
Trains a Random Forest classifier on synthetic transit features.

Usage:
    python -m app.ml.training.train_baseline
    # or from project root:
    python scripts/train_baseline.py
"""

import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


def generate_training_data(n_samples: int = 1000, seed: int = 42) -> tuple:
    """
    Generate synthetic training data for transit classification.

    Creates feature vectors with known labels for:
    - planet_candidate: realistic transit parameters
    - false_positive: weak/spurious signals
    - stellar_variability: periodic but non-transit
    - eclipsing_binary: deep eclipses
    - noise: random noise features

    Returns:
        Tuple of (features, labels).
    """
    rng = np.random.default_rng(seed)
    features = []
    labels = []

    samples_per_class = n_samples // 5

    # Planet candidates: moderate depth, reasonable period, high SDE
    for _ in range(samples_per_class):
        period = rng.uniform(0.5, 30.0)
        depth = rng.uniform(0.0005, 0.03)
        duration = rng.uniform(1.0, 8.0)
        sde = rng.uniform(7.0, 30.0)
        snr = sde * rng.uniform(0.8, 1.2)
        n_transits = max(1, int(27.0 / period))
        depth_sig = depth / 0.001 * rng.uniform(0.8, 1.5)
        odd_even = rng.uniform(0.0, 0.2)

        features.append([period, np.log10(depth), duration, sde, snr,
                         n_transits, depth_sig, odd_even])
        labels.append("planet_candidate")

    # False positives: low SDE, inconsistent
    for _ in range(samples_per_class):
        period = rng.uniform(0.3, 50.0)
        depth = rng.uniform(0.0001, 0.01)
        duration = rng.uniform(0.5, 20.0)
        sde = rng.uniform(2.0, 7.0)
        snr = sde * rng.uniform(0.5, 1.0)
        n_transits = rng.integers(1, 5)
        depth_sig = rng.uniform(0.5, 3.0)
        odd_even = rng.uniform(0.0, 0.8)

        features.append([period, np.log10(max(depth, 1e-10)), duration, sde,
                         snr, n_transits, depth_sig, odd_even])
        labels.append("false_positive")

    # Stellar variability: short period, moderate amplitude
    for _ in range(samples_per_class):
        period = rng.uniform(0.1, 5.0)
        depth = rng.uniform(0.002, 0.02)
        duration = rng.uniform(5.0, 20.0)  # Long "duration"
        sde = rng.uniform(3.0, 15.0)
        snr = sde * rng.uniform(0.7, 1.1)
        n_transits = max(1, int(27.0 / period))
        depth_sig = rng.uniform(1.0, 5.0)
        odd_even = rng.uniform(0.0, 0.3)

        features.append([period, np.log10(depth), duration, sde, snr,
                         n_transits, depth_sig, odd_even])
        labels.append("stellar_variability")

    # Eclipsing binaries: deep, often high odd/even
    for _ in range(samples_per_class):
        period = rng.uniform(0.5, 20.0)
        depth = rng.uniform(0.03, 0.5)
        duration = rng.uniform(1.0, 10.0)
        sde = rng.uniform(10.0, 50.0)
        snr = sde * rng.uniform(0.9, 1.3)
        n_transits = max(1, int(27.0 / period))
        depth_sig = depth / 0.001 * rng.uniform(0.8, 1.2)
        odd_even = rng.uniform(0.1, 1.0)

        features.append([period, np.log10(depth), duration, sde, snr,
                         n_transits, depth_sig, odd_even])
        labels.append("eclipsing_binary")

    # Noise: everything weak
    for _ in range(samples_per_class):
        period = rng.uniform(0.3, 50.0)
        depth = rng.uniform(0.00001, 0.001)
        duration = rng.uniform(0.1, 5.0)
        sde = rng.uniform(0.5, 4.0)
        snr = sde * rng.uniform(0.3, 1.0)
        n_transits = rng.integers(0, 3)
        depth_sig = rng.uniform(0.0, 2.0)
        odd_even = rng.uniform(0.0, 1.0)

        features.append([period, np.log10(max(depth, 1e-10)), duration, sde,
                         snr, n_transits, depth_sig, odd_even])
        labels.append("noise")

    return np.array(features), np.array(labels)


def train_and_save(model_dir: str = "ml_models", n_samples: int = 2000):
    """Train baseline classifier and save to disk."""
    print("=" * 60)
    print("ANVESHAK — Training Baseline Transit Classifier")
    print("=" * 60)

    # Generate data
    print("\nGenerating synthetic training data...")
    X, y = generate_training_data(n_samples=n_samples)
    print(f"  Total samples: {len(X)}")
    print(f"  Classes: {np.unique(y).tolist()}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train
    print("\nTraining Random Forest classifier...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    accuracy = float(np.mean(y_pred == y_test))
    print(f"Overall Accuracy: {accuracy:.4f}")

    # Save
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    output_path = model_path / "baseline_classifier.joblib"
    joblib.dump(clf, output_path)
    print(f"\nModel saved to: {output_path}")
    print("=" * 60)

    return clf, accuracy


if __name__ == "__main__":
    model_dir = sys.argv[1] if len(sys.argv) > 1 else "ml_models"
    train_and_save(model_dir)
