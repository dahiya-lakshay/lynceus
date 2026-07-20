from __future__ import annotations

import pandas as pd


BINARY_FEATURES = [
    "is_weekend",
    "is_new_receiver",
    "device_trusted",
    "cross_border",
    "high_risk_country"
]


REQUIRED_COLUMNS = [
    "amount",
    "currency",
    "payment_method",
    "merchant_category",
    "device_type",
    "origin_country",
    "destination_country",
    "hour",
    "day_of_week",
    "sender_account_age_days",
    "receiver_account_age_days",
    "sender_txn_count_24h",
    "receiver_txn_count_24h",
    "sender_avg_amount_30d",
    "receiver_avg_amount_30d",
    "velocity_score",
    "is_weekend",
    "is_new_receiver",
    "device_trusted",
    "cross_border",
    "high_risk_country"
]


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare incoming transaction data for inference.

    Performs exactly the same preprocessing steps that were
    applied before the fitted preprocessing pipeline during
    training.

    This function DOES NOT perform feature scaling,
    encoding, or imputation. Those are handled by the
    saved preprocessing_pipeline.joblib.
    """

    df = df.copy()

    # --------------------------------------------------
    # Remove timestamp if present
    # --------------------------------------------------

    if "timestamp" in df.columns:
        df = df.drop(columns="timestamp")

    # --------------------------------------------------
    # Validate required columns
    # --------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------
    # Convert binary columns
    # --------------------------------------------------

    df[BINARY_FEATURES] = (
        df[BINARY_FEATURES]
        .fillna(False)
        .astype("int8")
    )

    # --------------------------------------------------
    # Preserve training column order
    # --------------------------------------------------

    df = df[REQUIRED_COLUMNS]
    return df