from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction_repository import (
    TransactionRepository,
)


class FeatureEngineeringService:

    HIGH_RISK_COUNTRIES = {
        "KP",
        "IR",
        "SY",
        "AF",
    }

    @classmethod
    def build_features(
        cls,
        db: Session,
        transaction: Transaction,
    ) -> dict:

        return {

            # --------------------------
            # Transaction Features
            # --------------------------

            "amount": float(transaction.amount),

            "currency": transaction.currency,

            "payment_method": transaction.payment_method.value,

            "merchant_category": transaction.merchant_category.value,

            "device_type": transaction.device_type.value,

            "origin_country": transaction.origin_country,

            "destination_country": transaction.destination_country,

            "hour": transaction.created_at.hour,

            "day_of_week": transaction.created_at.weekday(),

            # --------------------------
            # User Features
            # --------------------------

            "sender_account_age_days":
                cls.get_sender_account_age(
                    db,
                    transaction.sender_id,
                ),

            "receiver_account_age_days":
                cls.get_receiver_account_age(
                    db,
                    transaction.receiver_id,
                ),

            # --------------------------
            # Transaction History
            # --------------------------

            "sender_txn_count_24h":
                TransactionRepository.count_sender_transactions_last_24h(
                    db,
                    transaction.sender_id,
                ),

            "receiver_txn_count_24h":
                TransactionRepository.count_receiver_transactions_last_24h(
                    db,
                    transaction.receiver_id,
                ),

            "sender_avg_amount_30d":
                float(
                    TransactionRepository.average_sender_amount_last_30d(
                        db,
                        transaction.sender_id,
                    )
                ),

            "receiver_avg_amount_30d":
                float(
                    TransactionRepository.average_receiver_amount_last_30d(
                        db,
                        transaction.receiver_id,
                    )
                ),

            # --------------------------
            # Derived Features
            # --------------------------

            "velocity_score":
                cls.calculate_velocity_score(
                    db,
                    transaction,
                ),

            "is_weekend":
                transaction.created_at.weekday() >= 5,

            "is_new_receiver":
                cls.is_new_receiver(
                    db,
                    transaction.sender_id,
                    transaction.receiver_id,
                ),

            "device_trusted":
                cls.is_device_trusted(
                    db,
                    transaction.sender_id,
                    transaction.device_id_hash,
                ),

            "cross_border":
                transaction.origin_country
                != transaction.destination_country,

            "high_risk_country":
                cls.is_high_risk_country(
                    transaction.destination_country,
                ),
        }

    # =====================================================
    # User Features
    # =====================================================

    @staticmethod
    def get_sender_account_age(
        db: Session,
        sender_id: int,
    ) -> int:

        user = db.get(User, sender_id)

        if user is None:
            return 0

        return (
            datetime.utcnow()
            - user.created_at
        ).days

    @staticmethod
    def get_receiver_account_age(
        db: Session,
        receiver_id: int,
    ) -> int:

        user = db.get(User, receiver_id)

        if user is None:
            return 0

        return (
            datetime.utcnow()
            - user.created_at
        ).days

    # =====================================================
    # Derived Features
    # =====================================================

    @staticmethod
    def calculate_velocity_score(
        db: Session,
        transaction: Transaction,
    ) -> float:

        sender_count = (
            TransactionRepository.count_sender_transactions_last_24h(
                db,
                transaction.sender_id,
            )
        )

        amount = float(transaction.amount)

        return round(
            sender_count * amount,
            2,
        )

    @staticmethod
    def is_new_receiver(
        db: Session,
        sender_id: int,
        receiver_id: int,
    ) -> bool:

        return not TransactionRepository.has_previous_transaction(
            db,
            sender_id,
            receiver_id,
        )

    @staticmethod
    def is_device_trusted(
        db: Session,
        sender_id: int,
        device_id_hash: str,
    ) -> bool:

        return TransactionRepository.has_seen_device(
            db,
            sender_id,
            device_id_hash,
        )

    @classmethod
    def is_high_risk_country(
        cls,
        country: str,
    ) -> bool:

        return country in cls.HIGH_RISK_COUNTRIES