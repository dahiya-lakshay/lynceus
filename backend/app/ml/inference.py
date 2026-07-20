from __future__ import annotations

from time import perf_counter
from typing import Any

import pandas as pd

from app.ml.model_loader import ModelLoader
from app.ml.preprocessing import prepare_dataframe


class FraudInference:
    """
    Production inference service for Lynceus.

    Workflow
    --------
    Incoming Transaction
            ↓
    Prepare DataFrame
            ↓
    Preprocessing Pipeline
            ↓
    ML Model
            ↓
    Fraud Probability
            ↓
    Threshold Decision
            ↓
    Response
    """

    @staticmethod
    def predict(
        transaction: dict[str, Any],
    ) -> dict[str, Any]:

        start_time = perf_counter()

        try:

            model = ModelLoader.get_model()

            preprocessor = ModelLoader.get_preprocessor()

            metadata = ModelLoader.get_metadata()

            threshold = metadata["optimal_threshold"]

            df = pd.DataFrame([transaction])

            df = prepare_dataframe(df)

            X = preprocessor.transform(df)

            fraud_probability = float(
                model.predict_proba(X)[0][1]
            )

            prediction = (
                "FRAUD"
                if fraud_probability >= threshold
                else "LEGITIMATE"
            )

            latency_ms = int(
                (perf_counter() - start_time) * 1000
            )

            return {
                "prediction": prediction,

                "fraud_probability": round(
                    fraud_probability,
                    4
                ),

                "risk_score": round(
                    fraud_probability * 100,
                    2
                ),

                "model_name": metadata["model_name"],
                "model_version": metadata["model_version"],
                "latency_ms": latency_ms
            }

        except Exception as exc:

            raise RuntimeError(
                f"Fraud inference failed: {exc}"
            ) from exc