from pathlib import Path

import joblib


class ModelLoader:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model is None:

            model_path = (
                Path(__file__).parent
                / "models"
                / "fraud_model.pkl"
            )

            if not model_path.exists():
                return None

            cls._model = joblib.load(
                model_path,
            )

        return cls._model