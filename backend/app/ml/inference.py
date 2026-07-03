from time import perf_counter

from app.ml.model_loader import ModelLoader


class FraudInference:

    @staticmethod
    def predict(
        *,
        amount: float,
    ) -> dict:

        start_time = perf_counter()

        model = ModelLoader.get_model()

        # Temporary fallback until a trained model exists
        if model is None:

            fraud_probability = (
                0.90 if amount >= 100000 else 0.08
            )

        else:

            features = [
                [
                    amount,
                ]
            ]

            fraud_probability = float(
                model.predict_proba(features)[0][1]
            )

        latency_ms = int(
            (perf_counter() - start_time) * 1000
        )

        risk_score = round(
            fraud_probability * 100,
            2,
        )

        prediction = (
            "FRAUD"
            if fraud_probability >= 0.5
            else "LEGITIMATE"
        )

        explanation = (
            "High fraud probability"
            if prediction == "FRAUD"
            else "Low fraud probability"
        )

        return {
            "fraud_probability": round(
                fraud_probability,
                4,
            ),
            "risk_score": risk_score,
            "prediction": prediction,
            "explanation": explanation,
            "latency_ms": latency_ms,
        }