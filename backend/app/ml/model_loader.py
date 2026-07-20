from pathlib import Path
import json
import joblib


class ModelLoader:

    _model = None
    _preprocessor = None
    _metadata = None

    ARTIFACT_DIR = Path(__file__).parent / "artifacts"

    MODEL_PATH = ARTIFACT_DIR / "best_model.joblib"

    PREPROCESSOR_PATH = (
        ARTIFACT_DIR / "preprocessing_pipeline.joblib"
    )

    METADATA_PATH = (
        ARTIFACT_DIR / "model_metadata.json"
    )

    @classmethod
    def get_model(cls):

        if cls._model is None:

            if not cls.MODEL_PATH.exists():

                raise FileNotFoundError(
                    f"Model not found: {cls.MODEL_PATH}"
                )

            cls._model = joblib.load(
                cls.MODEL_PATH
            )

        return cls._model

    @classmethod
    def get_preprocessor(cls):

        if cls._preprocessor is None:

            if not cls.PREPROCESSOR_PATH.exists():

                raise FileNotFoundError(
                    f"Preprocessor not found: {cls.PREPROCESSOR_PATH}"
                )

            cls._preprocessor = joblib.load(
                cls.PREPROCESSOR_PATH
            )

        return cls._preprocessor

    @classmethod
    def get_metadata(cls):

        if cls._metadata is None:

            if not cls.METADATA_PATH.exists():

                raise FileNotFoundError(
                    f"Metadata not found: {cls.METADATA_PATH}"
                )

            with open(cls.METADATA_PATH) as f:

                cls._metadata = json.load(f)

        return cls._metadata