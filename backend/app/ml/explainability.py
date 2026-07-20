from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap

from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


class ExplainabilityService:
    """
    Generates SHAP explanations for production fraud predictions.
    """

    _explainer = None

    @staticmethod
    def create_explainer(
        model: Any,
        background_data: pd.DataFrame | None = None,
    ):
        """
        Create the appropriate SHAP explainer.
        """

        if isinstance(
            model,
            (
                RandomForestClassifier,
                XGBClassifier,
                LGBMClassifier,
                CatBoostClassifier,
            ),
        ):
            return shap.TreeExplainer(model)

        if isinstance(model, LogisticRegression):

            if background_data is None:
                raise ValueError(
                    "Background data is required for LinearExplainer."
                )

            return shap.LinearExplainer(
                model,
                background_data,
            )

        if background_data is None:
            raise ValueError(
                "Background data is required for generic SHAP Explainer."
            )

        return shap.Explainer(
            model,
            background_data,
        )

    @classmethod
    def get_explainer(
        cls,
        model: Any,
        background_data: pd.DataFrame | None = None,
    ):
        """
        Lazily create and cache the SHAP explainer.
        """

        if cls._explainer is None:
            cls._explainer = cls.create_explainer(
                model,
                background_data,
            )

        return cls._explainer

    @staticmethod
    def explain_prediction(
        explainer: Any,
        X: Any,
        feature_names: list[str],
        top_n: int = 5,
    ) -> dict[str, Any]:
        """
        Explain a single prediction.
        """

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(
                X,
                columns=feature_names,
            )

        if len(X) != 1:
            raise ValueError(
                "Explainability supports exactly one prediction."
            )

        if len(feature_names) != X.shape[1]:
            raise ValueError(
                "Feature names do not match transformed feature count."
            )

        shap_values = explainer(X)

        values = shap_values.values[0]

        order = np.argsort(
            np.abs(values)
        )[::-1][:top_n]

        top_features = []

        for idx in order:

            impact = float(values[idx])

            top_features.append(
                {
                    "feature": feature_names[idx],
                    "impact": round(
                        impact,
                        6,
                    ),
                    "direction": (
                        "increase"
                        if impact > 0
                        else "decrease"
                    ),
                    "magnitude": round(
                        abs(impact),
                        6,
                    ),
                }
            )

        increased_risk = [
            feature["feature"]
            for feature in top_features
            if feature["impact"] > 0
        ]

        reduced_risk = [
            feature["feature"]
            for feature in top_features
            if feature["impact"] < 0
        ]

        explanation_parts = []

        if increased_risk:
            explanation_parts.append(
                "Increased fraud risk: "
                + ", ".join(increased_risk)
            )

        if reduced_risk:
            explanation_parts.append(
                "Reduced fraud risk: "
                + ", ".join(reduced_risk)
            )

        return {
            "top_features": top_features,
            "explanation": ". ".join(explanation_parts),
        }