"""
ANVESHAK — Model Registry
Tracks trained model versions, metadata, and artifacts.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.db_models import ModelVersion

logger = get_logger("ml.registry")


class ModelRegistry:
    """Manages ML model version tracking in the database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_model(
        self,
        name: str,
        algorithm: str,
        version: str,
        metrics: dict[str, Any],
        artifact_path: str,
        feature_list: list[str],
        confusion_matrix: Optional[list[list[int]]] = None,
        feature_importances: Optional[dict[str, float]] = None,
        training_dataset_id: Optional[int] = None,
    ) -> ModelVersion:
        """Register a new model version."""
        model = ModelVersion(
            name=name,
            algorithm=algorithm,
            version=version,
            training_dataset_id=training_dataset_id,
            metrics=metrics,
            artifact_path=artifact_path,
            feature_list=feature_list,
            confusion_matrix=confusion_matrix,
            feature_importances=feature_importances,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        logger.info("model_registered", name=name, version=version)
        return model

    async def get_latest_model(self, name: str) -> Optional[ModelVersion]:
        """Get the latest version of a named model."""
        result = await self.db.execute(
            select(ModelVersion)
            .where(ModelVersion.name == name)
            .order_by(desc(ModelVersion.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_models(self) -> list[ModelVersion]:
        """List all model versions."""
        result = await self.db.execute(
            select(ModelVersion).order_by(desc(ModelVersion.created_at))
        )
        return list(result.scalars().all())

    async def get_model_by_id(self, model_id: int) -> Optional[ModelVersion]:
        """Get a specific model version by ID."""
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.id == model_id)
        )
        return result.scalar_one_or_none()
