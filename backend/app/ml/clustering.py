"""
ANVESHAK — Clustering & PCA Module
KMeans clustering with PCA dimensionality reduction for exoplanet population analysis.
"""

from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from app.core.config import ML_ARTIFACTS_DIR
from app.core.logging import get_logger

logger = get_logger("ml.clustering")

CLUSTERING_FEATURES = [
    "orbital_period_days",
    "planet_radius_earth",
    "planet_mass_earth",
    "equilibrium_temp_k",
    "effective_temp_k",
    "stellar_radius_solar",
    "stellar_mass_solar",
]


class ClusteringEngine:
    """
    PCA + KMeans clustering for exoplanet population analysis.

    Identifies natural groupings in the exoplanet parameter space.
    """

    def __init__(self, n_clusters: int = 5, n_components: int = 2):
        self.n_clusters = n_clusters
        self.n_components = n_components
        self.kmeans = None
        self.pca = None
        self.scaler = StandardScaler()
        self.imputer = SimpleImputer(strategy="median")
        self.feature_names = CLUSTERING_FEATURES
        self.is_fitted = False
        self.cluster_stats = {}

    def fit_predict(
        self,
        df: pd.DataFrame,
        feature_names: Optional[list[str]] = None,
        n_clusters: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fit clustering model and return cluster assignments.

        Args:
            df: DataFrame with feature columns.
            feature_names: Features to cluster on.
            n_clusters: Number of clusters. None to auto-detect with elbow.

        Returns:
            DataFrame with cluster_id, pca_x, pca_y, distance_to_centroid.
        """
        if feature_names:
            self.feature_names = feature_names
        if n_clusters:
            self.n_clusters = n_clusters

        available = [f for f in self.feature_names if f in df.columns]
        if len(available) < 2:
            raise ValueError(f"Need at least 2 features. Available: {available}")

        self.feature_names = available
        X = df[available].values

        # Impute, scale
        X_imputed = self.imputer.fit_transform(X)
        X_scaled = self.scaler.fit_transform(X_imputed)

        # PCA
        n_comp = min(self.n_components, X_scaled.shape[1], X_scaled.shape[0])
        self.pca = PCA(n_components=n_comp, random_state=42)
        X_pca = self.pca.fit_transform(X_scaled)

        # Auto-select n_clusters using simple elbow heuristic
        if n_clusters is None:
            self.n_clusters = self._find_optimal_k(X_scaled, max_k=min(10, len(X_scaled) // 5))

        # KMeans
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300,
        )
        cluster_labels = self.kmeans.fit_predict(X_scaled)
        self.is_fitted = True

        # Compute distances to centroids
        distances = np.zeros(len(X_scaled))
        for i in range(len(X_scaled)):
            centroid = self.kmeans.cluster_centers_[cluster_labels[i]]
            distances[i] = np.linalg.norm(X_scaled[i] - centroid)

        # Cluster statistics
        self._compute_cluster_stats(df, available, cluster_labels)

        result = pd.DataFrame({
            "cluster_id": cluster_labels,
            "pca_x": X_pca[:, 0] if X_pca.shape[1] >= 1 else 0,
            "pca_y": X_pca[:, 1] if X_pca.shape[1] >= 2 else 0,
            "distance_to_centroid": distances,
        })

        logger.info(
            "clustering_complete",
            n_clusters=self.n_clusters,
            n_samples=len(df),
            features=len(available),
        )

        return result

    def _find_optimal_k(self, X: np.ndarray, max_k: int = 10) -> int:
        """Simple elbow method for selecting number of clusters."""
        max_k = max(2, min(max_k, len(X) - 1))
        inertias = []

        for k in range(2, max_k + 1):
            km = KMeans(n_clusters=k, random_state=42, n_init=5, max_iter=100)
            km.fit(X)
            inertias.append(km.inertia_)

        if len(inertias) < 2:
            return 3

        # Find elbow using second derivative
        diffs = np.diff(inertias)
        diffs2 = np.diff(diffs)

        if len(diffs2) > 0:
            optimal_k = np.argmax(diffs2) + 2  # +2 because we started at k=2
            optimal_k = min(optimal_k, max_k)
        else:
            optimal_k = 3

        return max(2, optimal_k)

    def _compute_cluster_stats(
        self,
        df: pd.DataFrame,
        features: list[str],
        labels: np.ndarray,
    ):
        """Compute summary statistics for each cluster."""
        self.cluster_stats = {}
        df_temp = df[features].copy()
        df_temp["cluster_id"] = labels

        for cluster_id in range(self.n_clusters):
            cluster_data = df_temp[df_temp["cluster_id"] == cluster_id]
            stats = {
                "size": int(len(cluster_data)),
                "mean": {},
                "std": {},
            }
            for feat in features:
                stats["mean"][feat] = float(cluster_data[feat].mean()) if not cluster_data[feat].isna().all() else None
                stats["std"][feat] = float(cluster_data[feat].std()) if not cluster_data[feat].isna().all() else None

            self.cluster_stats[int(cluster_id)] = stats

    def get_pca_explained_variance(self) -> list[float]:
        """Return explained variance ratios from PCA."""
        if self.pca is None:
            return []
        return self.pca.explained_variance_ratio_.tolist()

    def get_cluster_summary(self) -> dict[str, Any]:
        """Return cluster statistics."""
        return {
            "n_clusters": self.n_clusters,
            "features_used": self.feature_names,
            "explained_variance": self.get_pca_explained_variance(),
            "cluster_stats": self.cluster_stats,
        }

    def save(self, path: Optional[str] = None, version: str = "v1") -> str:
        """Save the fitted clustering model."""
        save_dir = Path(path) if path else ML_ARTIFACTS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)
        model_path = save_dir / f"clustering_{version}.joblib"

        joblib.dump({
            "kmeans": self.kmeans,
            "pca": self.pca,
            "scaler": self.scaler,
            "imputer": self.imputer,
            "feature_names": self.feature_names,
            "n_clusters": self.n_clusters,
            "cluster_stats": self.cluster_stats,
        }, model_path)

        logger.info("clustering_model_saved", path=str(model_path))
        return str(model_path)

    def load(self, path: Optional[str] = None, version: str = "v1") -> bool:
        """Load a fitted clustering model."""
        load_dir = Path(path) if path else ML_ARTIFACTS_DIR
        model_path = load_dir / f"clustering_{version}.joblib"

        if not model_path.exists():
            return False

        data = joblib.load(model_path)
        self.kmeans = data["kmeans"]
        self.pca = data["pca"]
        self.scaler = data["scaler"]
        self.imputer = data["imputer"]
        self.feature_names = data["feature_names"]
        self.n_clusters = data["n_clusters"]
        self.cluster_stats = data.get("cluster_stats", {})
        self.is_fitted = True

        logger.info("clustering_model_loaded", path=str(model_path))
        return True
