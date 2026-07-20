"""
Lynceus Synthetic Transaction Dataset Generator

"""

from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


# ==========================================================
# Configuration
# ==========================================================

RANDOM_SEED = 42

NUM_TRANSACTIONS = 100_000

TARGET_FRAUD_RATE = 0.02

OUTPUT_DIR = Path(__file__).parent.parent / "data"

OUTPUT_FILE = OUTPUT_DIR / "transactions.csv"

TRAIN_SPLIT = 0.70
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Fixed reference date for reproducible dataset generation
REFERENCE_DATE = datetime(2026, 1, 1)

# Type alias (item 22)
Transaction = Dict[str, Any]


# ==========================================================
# NOISE / DIFFICULTY CONFIG
# ==========================================================
# These four knobs control how separable fraud vs legitimate
# transactions are, i.e. how hard the classification problem is.
# Raise them to push model accuracy/AUC/F1 DOWN; lower them to push
# it back up toward v2's near-perfect behaviour.
#
# Rough guidance (LogReg/RF/XGBoost/LightGBM/CatBoost, 100k rows,
# 2% fraud rate):
#   All at 0                              -> ~98-100% (v2 behaviour)
#   Defaults below                        -> ~85-92% on AUC/F1/accuracy
#   Doubling all four                     -> ~75-85% (harder still)
#
# Actual numbers depend on your train/test split, model, and
# hyperparameters, so treat these as a starting point and re-tune
# after your first training run.

# Probability that any single fraud "marker" mutation inside a
# scenario is SKIPPED, so not every fraud row trips every associated
# risk rule.
FRAUD_MUTATION_SKIP_PROB = 0.27

# Fraction of legitimate transactions that get 1-3 risky-looking
# fields injected (untrusted device, new receiver, odd hour,
# elevated velocity) without being fraud.
LEGIT_LOOKALIKE_RATE = 0.085

# Relative Gaussian jitter (as a fraction of the field's value)
# applied to key numeric fields on every transaction.
FEATURE_JITTER_STD = 0.065

# Fraction of final labels flipped post-hoc (simulates labelling
# error / chargeback disputes), applied once on the full dataset
# after generation. Split into two class-conditional rates rather
# than one uniform rate: with only ~2% fraud, a single uniform rate
# would overwhelmingly corrupt the *legit* class (there are ~49x
# more of them) and silently blow up the apparent fraud rate. Real
# fraud labelling error is asymmetric anyway - missed/undetected
# fraud (false negatives baked into "ground truth") is far more
# common than a legit transaction wrongly confirmed as fraud.
LABEL_NOISE_RATE_FRAUD_TO_LEGIT = 0.09   # missed/undetected fraud
LABEL_NOISE_RATE_LEGIT_TO_FRAUD = 0.0045  # mistaken fraud confirmations


# ==========================================================
# Enums (item 21)
# ==========================================================

class CustomerType(str, Enum):
    STUDENT = "STUDENT"
    PROFESSIONAL = "PROFESSIONAL"
    BUSINESS = "BUSINESS"
    RETIRED = "RETIRED"
    TOURIST = "TOURIST"


class MerchantCategory(str, Enum):
    SHOPPING = "SHOPPING"
    TRAVEL = "TRAVEL"
    FOOD = "FOOD"
    HEALTHCARE = "HEALTHCARE"
    UTILITIES = "UTILITIES"
    ENTERTAINMENT = "ENTERTAINMENT"
    EDUCATION = "EDUCATION"
    FUEL = "FUEL"
    ELECTRONICS = "ELECTRONICS"
    OTHER = "OTHER"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    WALLET = "WALLET"


class DeviceType(str, Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"
    WINDOWS = "WINDOWS"
    MACOS = "MACOS"
    LINUX = "LINUX"
    WEB = "WEB"


class Country(str, Enum):
    IN = "IN"
    US = "US"
    GB = "GB"
    AE = "AE"
    SG = "SG"
    JP = "JP"
    DE = "DE"
    FR = "FR"
    NG = "NG"
    PK = "PK"
    RU = "RU"
    IR = "IR"
    KP = "KP"


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class FraudReason(str, Enum):
    LEGITIMATE = "LEGITIMATE"
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    CARD_TESTING = "CARD_TESTING"
    MONEY_MULE = "MONEY_MULE"
    STOLEN_CARD = "STOLEN_CARD"
    SYNTHETIC_IDENTITY = "SYNTHETIC_IDENTITY"


COUNTRIES: List[str] = [
    Country.IN.value,
    Country.US.value,
    Country.GB.value,
    Country.AE.value,
    Country.SG.value,
    Country.JP.value,
    Country.DE.value,
    Country.FR.value,
]

HIGH_RISK_COUNTRIES: List[str] = [
    Country.NG.value,
    Country.PK.value,
    Country.RU.value,
    Country.IR.value,
    Country.KP.value,
]

DEVICE_TYPES: List[str] = [d.value for d in DeviceType]

PAYMENT_METHODS: List[str] = [p.value for p in PaymentMethod]


# ==========================================================
# Customer / Merchant Profiles (item 1 fix: dataclass attrs)
# ==========================================================

@dataclass(frozen=True)
class CustomerProfile:
    """
    Represents a realistic customer archetype.
    """

    name: str
    avg_amount: int
    active_start_hour: int
    active_end_hour: int
    preferred_payment_methods: List[str]
    preferred_merchants: List[str]
    international_probability: float
    weekday_weights: List[float]  # Mon(0) .. Sun(6)


@dataclass(frozen=True)
class MerchantProfile:
    """
    Represents a merchant category.
    """

    min_amount: int
    max_amount: int


CUSTOMER_PROFILES: List[CustomerProfile] = [

    CustomerProfile(
        name=CustomerType.STUDENT.value,
        avg_amount=1500,
        active_start_hour=17,
        active_end_hour=1,
        preferred_payment_methods=[
            PaymentMethod.UPI.value,
            PaymentMethod.WALLET.value,
        ],
        preferred_merchants=[
            MerchantCategory.FOOD.value,
            MerchantCategory.ENTERTAINMENT.value,
            MerchantCategory.SHOPPING.value,
        ],
        international_probability=0.01,
        # more activity Saturday / Sunday
        weekday_weights=[1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 1.5],
    ),

    CustomerProfile(
        name=CustomerType.PROFESSIONAL.value,
        avg_amount=7000,
        active_start_hour=8,
        active_end_hour=22,
        preferred_payment_methods=[
            PaymentMethod.UPI.value,
            PaymentMethod.CARD.value,
            PaymentMethod.BANK_TRANSFER.value,
        ],
        preferred_merchants=[
            MerchantCategory.SHOPPING.value,
            MerchantCategory.TRAVEL.value,
            MerchantCategory.UTILITIES.value,
            MerchantCategory.FOOD.value,
        ],
        international_probability=0.05,
        # less activity Sunday
        weekday_weights=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6],
    ),

    CustomerProfile(
        name=CustomerType.BUSINESS.value,
        avg_amount=30000,
        active_start_hour=8,
        active_end_hour=18,
        preferred_payment_methods=[
            PaymentMethod.BANK_TRANSFER.value,
            PaymentMethod.CARD.value,
        ],
        preferred_merchants=[
            MerchantCategory.TRAVEL.value,
            MerchantCategory.UTILITIES.value,
            MerchantCategory.HEALTHCARE.value,
        ],
        international_probability=0.25,
        # Monday - Friday only
        weekday_weights=[1.0, 1.0, 1.0, 1.0, 1.0, 0.1, 0.05],
    ),

    CustomerProfile(
        name=CustomerType.RETIRED.value,
        avg_amount=2500,
        active_start_hour=9,
        active_end_hour=18,
        preferred_payment_methods=[
            PaymentMethod.UPI.value,
            PaymentMethod.CARD.value,
        ],
        preferred_merchants=[
            MerchantCategory.HEALTHCARE.value,
            MerchantCategory.UTILITIES.value,
            MerchantCategory.FOOD.value,
        ],
        international_probability=0.01,
        # uniform across the week
        weekday_weights=[1.0] * 7,
    ),

    CustomerProfile(
        name=CustomerType.TOURIST.value,
        avg_amount=12000,
        active_start_hour=7,
        active_end_hour=23,
        preferred_payment_methods=[
            PaymentMethod.CARD.value,
            PaymentMethod.WALLET.value,
        ],
        preferred_merchants=[
            MerchantCategory.TRAVEL.value,
            MerchantCategory.FOOD.value,
            MerchantCategory.SHOPPING.value,
        ],
        international_probability=0.80,
        # Friday - Sunday spike
        weekday_weights=[0.8, 0.8, 0.8, 0.8, 1.3, 1.5, 1.5],
    ),
]

CUSTOMER_PROFILE_BY_NAME: Dict[str, CustomerProfile] = {
    p.name: p for p in CUSTOMER_PROFILES
}

MERCHANTS: Dict[str, MerchantProfile] = {

    MerchantCategory.SHOPPING.value: MerchantProfile(500, 15000),
    MerchantCategory.TRAVEL.value: MerchantProfile(3000, 80000),
    MerchantCategory.FOOD.value: MerchantProfile(100, 3000),
    MerchantCategory.HEALTHCARE.value: MerchantProfile(500, 100000),
    MerchantCategory.UTILITIES.value: MerchantProfile(200, 10000),
    MerchantCategory.ENTERTAINMENT.value: MerchantProfile(200, 8000),
    MerchantCategory.EDUCATION.value: MerchantProfile(5000, 150000),
    MerchantCategory.FUEL.value: MerchantProfile(300, 5000),
    MerchantCategory.ELECTRONICS.value: MerchantProfile(1000, 200000),
    MerchantCategory.OTHER.value: MerchantProfile(100, 20000),
}

# ==========================================================
# Behavioural correlation tables (item 5, 6, 9, 10)
# ==========================================================

# item 9: merchant categories have a "peak" set of hours
MERCHANT_PEAK_HOURS: Dict[str, List[int]] = {
    MerchantCategory.FOOD.value: [12, 13, 19, 20, 21],
    MerchantCategory.TRAVEL.value: [6, 7, 8, 9, 17, 18],
    MerchantCategory.SHOPPING.value: [14, 15, 16, 17, 18],
    MerchantCategory.UTILITIES.value: list(range(9, 18)),
    MerchantCategory.HEALTHCARE.value: list(range(9, 18)),
    MerchantCategory.ENTERTAINMENT.value: [18, 19, 20, 21, 22, 23],
    MerchantCategory.EDUCATION.value: list(range(9, 17)),
    MerchantCategory.FUEL.value: list(range(7, 20)),
    MerchantCategory.ELECTRONICS.value: list(range(11, 20)),
    MerchantCategory.OTHER.value: list(range(0, 24)),
}

# item 5: merchant nudges the payment method used
MERCHANT_PAYMENT_BIAS: Dict[str, Tuple[str, float]] = {
    MerchantCategory.TRAVEL.value: (PaymentMethod.CARD.value, 2.5),
    MerchantCategory.FOOD.value: (PaymentMethod.UPI.value, 2.5),
    MerchantCategory.UTILITIES.value: (PaymentMethod.BANK_TRANSFER.value, 2.5),
    MerchantCategory.HEALTHCARE.value: (PaymentMethod.CARD.value, 1.8),
    MerchantCategory.ELECTRONICS.value: (PaymentMethod.CARD.value, 1.8),
    MerchantCategory.EDUCATION.value: (PaymentMethod.BANK_TRANSFER.value, 1.8),
    MerchantCategory.SHOPPING.value: (PaymentMethod.UPI.value, 1.3),
    MerchantCategory.ENTERTAINMENT.value: (PaymentMethod.WALLET.value, 1.5),
    MerchantCategory.FUEL.value: (PaymentMethod.UPI.value, 1.3),
    MerchantCategory.OTHER.value: (PaymentMethod.CARD.value, 1.0),
}

# item 10: device nudges the payment method used
DEVICE_PAYMENT_BIAS: Dict[str, Tuple[str, float]] = {
    DeviceType.ANDROID.value: (PaymentMethod.UPI.value, 2.0),
    DeviceType.IOS.value: (PaymentMethod.CARD.value, 1.8),
    DeviceType.WINDOWS.value: (PaymentMethod.BANK_TRANSFER.value, 1.6),
    DeviceType.MACOS.value: (PaymentMethod.BANK_TRANSFER.value, 1.4),
    DeviceType.LINUX.value: (PaymentMethod.BANK_TRANSFER.value, 1.3),
    DeviceType.WEB.value: (PaymentMethod.CARD.value, 1.3),
}

# item 6: destination currency for cross-border transactions
COUNTRY_CURRENCY: Dict[str, str] = {
    Country.IN.value: Currency.INR.value,
    Country.US.value: Currency.USD.value,
    Country.GB.value: Currency.GBP.value,
    Country.DE.value: Currency.EUR.value,
    Country.FR.value: Currency.EUR.value,
}

# item 8: monthly salary-cycle spend boost, days 1-5 of the month
SALARY_CYCLE_DAYS = {1, 2, 3, 4, 5}
SALARY_CYCLE_PROFILE_BOOST = {
    CustomerType.PROFESSIONAL.value: 1.7,
    CustomerType.BUSINESS.value: 1.4,
    CustomerType.STUDENT.value: 1.1,
    CustomerType.RETIRED.value: 1.2,
    CustomerType.TOURIST.value: 1.0,
}
SALARY_CYCLE_MERCHANTS = {
    MerchantCategory.SHOPPING.value,
    MerchantCategory.UTILITIES.value,
}
SALARY_CYCLE_MERCHANT_BOOST = 1.8


# ==========================================================
# Fraud scenario config (item 12)
# ==========================================================

FRAUD_SCENARIO_DISTRIBUTION: Dict[str, int] = {
    FraudReason.ACCOUNT_TAKEOVER.value: 30,
    FraudReason.CARD_TESTING.value: 25,
    FraudReason.MONEY_MULE.value: 20,
    FraudReason.STOLEN_CARD.value: 15,
    FraudReason.SYNTHETIC_IDENTITY.value: 10,
}


# ==========================================================
# Risk engine config (item 14)
# ==========================================================
#
# Each entry: reason -> (weight, condition_fn)
# condition_fn receives the transaction dict and returns bool.
# Kept as simple, independent, thresholded rules. Multi-field
# *interaction* rules are still defined explicitly further down
# (they read more naturally as code than as a flat rule table).

RISK_RULES: Dict[str, Tuple[int, Callable[[Transaction], bool]]] = {
    "ABNORMAL_AMOUNT": (
        18,
        lambda t: t["amount"] > t["sender_avg_amount_30d"] * 4,
    ),
    "HIGH_AMOUNT": (
        10,
        lambda t: (
            t["sender_avg_amount_30d"] * 2
            < t["amount"]
            <= t["sender_avg_amount_30d"] * 4
        ),
    ),
    "UNTRUSTED_DEVICE": (
        15,
        lambda t: not t["device_trusted"],
    ),
    "NEW_RECEIVER": (
        12,
        lambda t: t["is_new_receiver"],
    ),
    "NEW_RECEIVER_ACCOUNT": (
        10,
        lambda t: t["receiver_account_age_days"] < 30,
    ),
    "CROSS_BORDER": (
        12,
        lambda t: t["cross_border"],
    ),
    "HIGH_RISK_COUNTRY": (
        18,
        lambda t: t["high_risk_country"],
    ),
    "HIGH_RISK_MERCHANT": (
        8,
        lambda t: t["merchant_category"] == MerchantCategory.ELECTRONICS.value,
    ),
    "TRAVEL_MERCHANT": (
        5,
        lambda t: t["merchant_category"] == MerchantCategory.TRAVEL.value,
    ),
    "HIGH_TXN_VOLUME": (
        15,
        lambda t: t["sender_txn_count_24h"] > 40,
    ),
    "HIGH_RECEIVER_VOLUME": (
        10,
        lambda t: t["receiver_txn_count_24h"] > 35,
    ),
    "HIGH_VELOCITY": (
        20,
        lambda t: t["velocity_score"] > 0.90,
    ),
    "ELEVATED_VELOCITY": (
        10,
        lambda t: 0.75 < t["velocity_score"] <= 0.90,
    ),
    "NIGHT_TRANSACTION": (
        8,
        lambda t: t["hour"] <= 5,
    ),
    "NEW_ACCOUNT": (
        15,
        lambda t: t["sender_account_age_days"] < 30,
    ),
    "UNTRUSTED_CARD_USAGE": (
        8,
        lambda t: (
            t["payment_method"] == PaymentMethod.CARD.value
            and not t["device_trusted"]
        ),
    ),
    "INTERNATIONAL_BANK_TRANSFER": (
        6,
        lambda t: (
            t["payment_method"] == PaymentMethod.BANK_TRANSFER.value
            and t["cross_border"]
        ),
    ),
}

# Interaction rules (multi-field combinations) - kept as code, not
# a flat table, since they combine >1 pre-computed condition.
INTERACTION_RULES: List[Tuple[str, int, Callable[[Transaction], bool]]] = [
    (
        "HIGH_RISK_TRANSFER",
        10,
        lambda t: t["cross_border"] and t["high_risk_country"],
    ),
    (
        "NEW_DEVICE_NEW_RECEIVER",
        10,
        lambda t: t["is_new_receiver"] and not t["device_trusted"],
    ),
    (
        "LARGE_FAST_TRANSFER",
        15,
        lambda t: (
            t["amount"] > t["sender_avg_amount_30d"] * 4
            and t["velocity_score"] > 0.90
        ),
    ),
    (
        "NEW_ACCOUNT_NEW_RECEIVER",
        10,
        lambda t: t["sender_account_age_days"] < 30 and t["is_new_receiver"],
    ),
    (
        "HIGH_VALUE_ELECTRONICS",
        12,
        lambda t: (
            t["merchant_category"] == MerchantCategory.ELECTRONICS.value
            and t["amount"] > 50000
        ),
    ),
]


# ==========================================================
# Weekday-weighted timestamp sampling (item 7)
# ==========================================================

def _build_weighted_day_offsets(
    profile: CustomerProfile,
) -> Tuple[List[int], List[float]]:
    """
    Precompute (day_offset, weight) pairs for the last 365 days,
    weighted by the profile's weekday preference and the monthly
    salary cycle (item 8).
    """

    offsets: List[int] = []
    weights: List[float] = []

    boost = SALARY_CYCLE_PROFILE_BOOST.get(profile.name, 1.0)

    for days_back in range(0, 366):
        date = REFERENCE_DATE - timedelta(days=days_back)

        weight = profile.weekday_weights[date.weekday()]

        if date.day in SALARY_CYCLE_DAYS:
            weight *= boost

        offsets.append(days_back)
        weights.append(weight)

    return offsets, weights


_WEIGHTED_DAY_OFFSETS: Dict[str, Tuple[List[int], List[float]]] = {
    profile.name: _build_weighted_day_offsets(profile)
    for profile in CUSTOMER_PROFILES
}


# ==========================================================
# Customer Behaviour Generator
# ==========================================================

def random_customer_profile() -> CustomerProfile:
    """
    Select a realistic customer profile.
    """

    return random.choices(
        CUSTOMER_PROFILES,
        weights=[30, 40, 10, 15, 5],
        k=1,
    )[0]


def random_customer_hour(profile: CustomerProfile) -> int:
    """
    Generate an hour based on the customer's active period.
    """

    start = profile.active_start_hour
    end = profile.active_end_hour

    if start <= end:
        return random.randint(start, end)

    hours = list(range(start, 24)) + list(range(0, end + 1))

    return random.choice(hours)


def random_customer_timestamp(profile: CustomerProfile) -> datetime:
    """
    Generate a realistic timestamp.

    Day-of-week and monthly salary-cycle effects (items 7 & 8) are
    applied via precomputed weights; the hour still comes from the
    profile's active-hours window.
    """

    offsets, weights = _WEIGHTED_DAY_OFFSETS[profile.name]

    days_back = random.choices(offsets, weights=weights, k=1)[0]

    hour = random_customer_hour(profile)

    return (
        REFERENCE_DATE
        - timedelta(days=days_back)
    ).replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


def random_merchant(profile: CustomerProfile, timestamp: datetime) -> str:
    """
    Select merchant category.

    Combines the customer's preferred merchants (item baseline),
    a time-of-day peak-hour boost (item 9), and a salary-cycle
    boost for shopping/utilities in the first days of the month
    (item 8).
    """

    hour = timestamp.hour
    day_of_month = timestamp.day

    if random.random() < 0.80:
        candidates = profile.preferred_merchants
    else:
        candidates = [
            merchant
            for merchant in MERCHANTS
            if merchant not in profile.preferred_merchants
        ]

    weights = []

    for merchant in candidates:
        weight = 1.0

        if hour in MERCHANT_PEAK_HOURS.get(merchant, []):
            weight *= 2.0

        if (
            day_of_month in SALARY_CYCLE_DAYS
            and merchant in SALARY_CYCLE_MERCHANTS
        ):
            weight *= SALARY_CYCLE_MERCHANT_BOOST

        weights.append(weight)

    return random.choices(candidates, weights=weights, k=1)[0]


def random_payment_method(profile: CustomerProfile, merchant: str, device: str) -> str:
    """
    Select a payment method.

    Baseline comes from customer preference, then nudged by the
    merchant category (item 5) and the device type (item 10).
    """

    weights = {method: 0.1 for method in PAYMENT_METHODS}

    for method in profile.preferred_payment_methods:
        weights[method] += 3.0

    merchant_method, merchant_boost = MERCHANT_PAYMENT_BIAS.get(
        merchant, (None, 1.0)
    )
    if merchant_method:
        weights[merchant_method] *= merchant_boost

    device_method, device_boost = DEVICE_PAYMENT_BIAS.get(
        device, (None, 1.0)
    )
    if device_method:
        weights[device_method] *= device_boost

    methods = list(weights.keys())
    method_weights = list(weights.values())

    return random.choices(methods, weights=method_weights, k=1)[0]


def random_amount(profile: CustomerProfile, merchant: str) -> float:
    """
    Generate a realistic transaction amount.
    """

    limits = MERCHANTS[merchant]

    minimum = limits.min_amount
    maximum = limits.max_amount

    mean = max(profile.avg_amount, minimum)

    sigma = max(mean * 0.35, minimum * 0.25)

    amount = np.random.normal(loc=mean, scale=sigma)

    amount = np.clip(amount, minimum, maximum)

    return round(float(amount), 2)


def random_origin_country(profile: CustomerProfile) -> str:
    """
    Select origin country.
    """

    if profile.name == CustomerType.TOURIST.value:
        return random.choice(COUNTRIES)

    return random.choices(
        COUNTRIES,
        weights=[80, 5, 3, 4, 3, 2, 2, 1],
        k=1,
    )[0]


def random_destination_country(
    profile: CustomerProfile,
    origin_country: str,
) -> str:
    """
    Destination country depends on customer behaviour.
    """

    if random.random() > profile.international_probability:
        return origin_country

    return random.choice(COUNTRIES + HIGH_RISK_COUNTRIES)


def random_currency(
    origin_country: str,
    destination_country: str,
    cross_border: bool,
) -> str:
    """
    Currency usually matches the origin country, but cross-border
    transactions are frequently settled in the destination /
    settlement currency instead (item 6).
    """

    if cross_border and random.random() < 0.65:
        return COUNTRY_CURRENCY.get(destination_country, Currency.USD.value)

    return COUNTRY_CURRENCY.get(origin_country, Currency.USD.value)


def random_device_type(profile: CustomerProfile) -> str:
    """
    Device preference varies across profiles.
    """

    if profile.name == CustomerType.BUSINESS.value:
        return random.choices(DEVICE_TYPES, weights=[25, 5, 30, 25, 10, 5], k=1)[0]

    if profile.name == CustomerType.STUDENT.value:
        return random.choices(DEVICE_TYPES, weights=[60, 25, 3, 2, 2, 8], k=1)[0]

    return random.choice(DEVICE_TYPES)


def random_device_trusted(profile: CustomerProfile) -> bool:
    """
    Most genuine users transact using trusted devices.
    """

    probability = {
        CustomerType.STUDENT.value: 0.88,
        CustomerType.PROFESSIONAL.value: 0.95,
        CustomerType.BUSINESS.value: 0.97,
        CustomerType.RETIRED.value: 0.96,
        CustomerType.TOURIST.value: 0.80,
    }

    return random.random() < probability[profile.name]


def random_account_age(profile: CustomerProfile) -> int:
    """
    Generate account age based on customer profile.
    """

    if profile.name == CustomerType.STUDENT.value:
        return random.randint(30, 1500)

    if profile.name == CustomerType.PROFESSIONAL.value:
        return random.randint(365, 3650)

    if profile.name == CustomerType.BUSINESS.value:
        return random.randint(730, 5000)

    if profile.name == CustomerType.RETIRED.value:
        return random.randint(1000, 5000)

    return random.randint(30, 1500)


def random_transaction_count(profile: CustomerProfile) -> int:
    """
    Number of transactions in the previous 24 hours.
    """

    if profile.name == CustomerType.BUSINESS.value:
        return random.randint(10, 60)

    if profile.name == CustomerType.PROFESSIONAL.value:
        return random.randint(2, 20)

    if profile.name == CustomerType.STUDENT.value:
        return random.randint(1, 15)

    if profile.name == CustomerType.RETIRED.value:
        return random.randint(0, 8)

    return random.randint(1, 25)


def random_average_amount(profile: CustomerProfile) -> float:
    """
    Historical average transaction amount.
    """

    variation = np.random.normal(profile.avg_amount, profile.avg_amount * 0.25)

    return round(max(100, variation), 2)


def random_velocity_score(txn_count: int) -> float:
    """
    Velocity score derived from transaction count.
    """

    score = min(txn_count / 50, 1.0)

    score += random.uniform(-0.05, 0.05)

    score = max(0.0, min(score, 1.0))

    return round(score, 3)


# ==========================================================
# Noise / difficulty engine
# ==========================================================

def _skip_marker(skip_prob: float = FRAUD_MUTATION_SKIP_PROB) -> bool:
    """
    Returns True if a given fraud "marker" mutation should be
    SKIPPED for this transaction (i.e. left at its legitimate-
    looking baseline value). Used inside apply_fraud_scenario so
    fraud rows don't trip every associated risk rule every time.
    """

    return random.random() < skip_prob


def apply_feature_jitter(transaction: Transaction) -> Transaction:
    """
    Add small relative Gaussian noise to key numeric fields, on
    every transaction (fraud and legitimate alike). This blurs the
    exact thresholds used by RISK_RULES so a model can't just learn
    those cutoffs and get a perfect split.
    """

    def jitter(value: float, minimum: float = 0.0) -> float:
        noisy = value * (1 + np.random.normal(0, FEATURE_JITTER_STD))
        return max(minimum, noisy)

    transaction["amount"] = round(jitter(transaction["amount"], minimum=1.0), 2)

    transaction["sender_avg_amount_30d"] = round(
        jitter(transaction["sender_avg_amount_30d"], minimum=50.0), 2
    )
    transaction["receiver_avg_amount_30d"] = round(
        jitter(transaction["receiver_avg_amount_30d"], minimum=50.0), 2
    )

    transaction["velocity_score"] = round(
        min(1.0, max(0.0, jitter(transaction["velocity_score"] + 1e-6))), 3
    )

    transaction["sender_account_age_days"] = max(
        1, int(round(jitter(transaction["sender_account_age_days"], minimum=1)))
    )
    transaction["receiver_account_age_days"] = max(
        1, int(round(jitter(transaction["receiver_account_age_days"], minimum=1)))
    )

    transaction["sender_txn_count_24h"] = max(
        0, int(round(jitter(transaction["sender_txn_count_24h"] + 0.5)))
    )
    transaction["receiver_txn_count_24h"] = max(
        0, int(round(jitter(transaction["receiver_txn_count_24h"] + 0.5)))
    )

    return transaction


def inject_legit_lookalike(transaction: Transaction) -> Transaction:
    """
    Take a genuinely legitimate transaction and, with some
    probability, nudge 1-3 fields toward "risky-looking" values
    without changing its fraud label. This is what creates real
    false-positive pressure for a downstream classifier - without
    it, "looks risky" and "is fraud" are almost the same thing.
    """

    if random.random() >= LEGIT_LOOKALIKE_RATE:
        return transaction

    possible_nudges: List[Callable[[Transaction], None]] = [
        lambda t: t.__setitem__("device_trusted", False),
        lambda t: t.__setitem__("is_new_receiver", True),
        lambda t: t.__setitem__("hour", random.randint(0, 4)),
        lambda t: t.__setitem__(
            "velocity_score", round(random.uniform(0.70, 0.95), 3)
        ),
        lambda t: t.__setitem__(
            "receiver_account_age_days", random.randint(1, 45)
        ),
        lambda t: t.__setitem__(
            "amount", round(t["amount"] * random.uniform(2.0, 3.5), 2)
        ),
        lambda t: t.__setitem__(
            "sender_txn_count_24h", random.randint(30, 45)
        ),
    ]

    num_nudges = random.randint(1, 3)
    chosen = random.sample(possible_nudges, k=num_nudges)

    for nudge in chosen:
        nudge(transaction)

    # keep day_of_week / is_weekend consistent if hour changed the
    # "night transaction" flag - nothing else derives from hour here,
    # so no further reconciliation is needed.

    return transaction


def apply_label_noise(
    df: pd.DataFrame,
    fraud_to_legit_rate: float = LABEL_NOISE_RATE_FRAUD_TO_LEGIT,
    legit_to_fraud_rate: float = LABEL_NOISE_RATE_LEGIT_TO_FRAUD,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Flip a random subset of final fraud_label values, simulating
    analyst/chargeback labelling error. Applied once, after the
    full dataset (with all features) has already been generated,
    so the flipped label is genuinely inconsistent with the row's
    features - this is what puts a hard ceiling on achievable
    model accuracy, independent of model quality.

    Uses two separate class-conditional rates instead of one
    uniform rate, since with a low base fraud rate a single uniform
    rate would corrupt mostly-legit rows into "fraud" and distort
    the overall fraud rate (see module docstring).
    """

    rng = np.random.default_rng(seed)

    df = df.copy()
    df["label_noise_applied"] = False

    fraud_idx = df.index[df["fraud_label"] == 1].values
    legit_idx = df.index[df["fraud_label"] == 0].values

    num_fraud_flips = int(round(len(fraud_idx) * fraud_to_legit_rate))
    num_legit_flips = int(round(len(legit_idx) * legit_to_fraud_rate))

    if num_fraud_flips > 0:
        flip_idx = rng.choice(fraud_idx, size=num_fraud_flips, replace=False)
        df.loc[flip_idx, "fraud_label"] = 0
        df.loc[flip_idx, "label_noise_applied"] = True

    if num_legit_flips > 0:
        flip_idx = rng.choice(legit_idx, size=num_legit_flips, replace=False)
        df.loc[flip_idx, "fraud_label"] = 1
        df.loc[flip_idx, "label_noise_applied"] = True

    return df



# ==========================================================
# Transaction Generator
# ==========================================================

def generate_legitimate_transaction() -> Transaction:
    """
    Generate one realistic, non-fraud-adjusted transaction.

    This is the "baseline" that the fraud engine will later copy
    and mutate (item 13) - fraud status is never decided before
    this baseline exists, so the legitimate distribution is never
    contaminated by the fraud branch.
    """

    profile = random_customer_profile()

    timestamp = random_customer_timestamp(profile)

    merchant = random_merchant(profile, timestamp)

    device = random_device_type(profile)

    payment_method = random_payment_method(profile, merchant, device)

    origin_country = random_origin_country(profile)

    destination_country = random_destination_country(profile, origin_country)

    cross_border = origin_country != destination_country

    sender_txn_count = random_transaction_count(profile)

    receiver_txn_count = random.randint(0, 40)

    amount = random_amount(profile, merchant)

    sender_average = random_average_amount(profile)

    receiver_average = round(random.uniform(500, 20000), 2)

    sender_account_age = random_account_age(profile)

    receiver_account_age = random.randint(30, 5000)

    velocity_score = random_velocity_score(sender_txn_count)

    transaction: Transaction = {

        # Customer metadata (kept in full dataset, dropped from
        # the ML training set - item 2)
        "customer_profile": profile.name,

        # Transaction
        "amount": amount,
        "currency": random_currency(
            origin_country, destination_country, cross_border
        ),
        "payment_method": payment_method,

        # Time
        "timestamp": timestamp,
        "hour": timestamp.hour,
        "day_of_week": timestamp.weekday(),
        "is_weekend": timestamp.weekday() >= 5,

        # Accounts
        "sender_account_age_days": sender_account_age,
        "receiver_account_age_days": receiver_account_age,

        # Behaviour
        "sender_txn_count_24h": sender_txn_count,
        "receiver_txn_count_24h": receiver_txn_count,

        "sender_avg_amount_30d": sender_average,
        "receiver_avg_amount_30d": receiver_average,

        "is_new_receiver": random.random() < 0.12,

        # Geography
        "origin_country": origin_country,
        "destination_country": destination_country,

        "cross_border": cross_border,

        "high_risk_country": destination_country in HIGH_RISK_COUNTRIES,

        # Merchant
        "merchant_category": merchant,

        # Device
        "device_type": device,

        "device_trusted": random_device_trusted(profile),

        # Behaviour score
        "velocity_score": velocity_score,
    }

    return transaction


def generate_transaction() -> Transaction:
    """
    Generate one transaction and decide, then apply, its fraud
    status (generate -> copy -> inject, item 13).
    """

    baseline = generate_legitimate_transaction()

    is_fraud = random.random() <= TARGET_FRAUD_RATE

    if not is_fraud:
        transaction = baseline
        transaction["fraud_reason"] = FraudReason.LEGITIMATE.value
        transaction["fraud_label"] = 0

        # Difficulty engine: some legit transactions get risky-
        # looking fields injected, then everyone gets feature jitter.
        transaction = inject_legit_lookalike(transaction)
        transaction = apply_feature_jitter(transaction)

        risk_score, reasons, contributions = calculate_risk_score(transaction)

        transaction["risk_score"] = risk_score
        transaction["risk_factors"] = reasons
        transaction["risk_contributions"] = contributions
        transaction["fraud_probability"] = min(
            calculate_fraud_probability(risk_score), 0.35
        )

        return transaction

    # Fraud branch: mutate a *copy* of the legitimate baseline,
    # never the baseline itself.
    transaction = copy.deepcopy(baseline)

    scenario = random.choices(
        list(FRAUD_SCENARIO_DISTRIBUTION.keys()),
        weights=list(FRAUD_SCENARIO_DISTRIBUTION.values()),
        k=1,
    )[0]

    transaction["fraud_reason"] = scenario
    transaction = apply_fraud_scenario(transaction, scenario)

    # Difficulty engine: jitter fraud rows too, so their features
    # don't sit at suspiciously "round" mutated values either.
    transaction = apply_feature_jitter(transaction)

    # Prevent unrealistic transaction amounts
    transaction["amount"] = min(transaction["amount"], 500000)

    risk_score, reasons, contributions = calculate_risk_score(transaction)

    transaction["risk_score"] = risk_score
    transaction["risk_factors"] = reasons
    transaction["risk_contributions"] = contributions
    transaction["fraud_probability"] = max(
        calculate_fraud_probability(risk_score), 0.70
    )
    transaction["fraud_label"] = 1

    return transaction


# ==========================================================
# Fraud Scenario Engine (item 11: coherent "attack playbooks")
# ==========================================================

def apply_fraud_scenario(transaction: Transaction, scenario: str) -> Transaction:
    """
    Mutate a transaction into a coherent fraud "playbook", where
    the mutated fields reinforce each other instead of being
    independently randomized.

    Each marker mutation is gated by `_skip_marker()` so that not
    every fraud transaction trips every associated risk rule -
    real fraud is inconsistent and partially disguised, not a
    perfect checklist match. Multiplier ranges are also shrunk
    relative to v2 so mutated values sometimes overlap the
    legitimate distribution instead of always sitting far outside it.
    """

    if scenario == FraudReason.ACCOUNT_TAKEOVER.value:
        # New device, done at night, drains the account fast into
        # a receiver that has never been paid before.
        if not _skip_marker():
            transaction["device_trusted"] = False
        if not _skip_marker():
            transaction["is_new_receiver"] = True
        if not _skip_marker():
            transaction["hour"] = random.randint(0, 5)
        if not _skip_marker():
            transaction["amount"] *= random.uniform(1.3, 3.0)
        if not _skip_marker():
            transaction["sender_txn_count_24h"] = random.randint(15, 45)
        if not _skip_marker():
            transaction["velocity_score"] = round(random.uniform(0.55, 0.95), 3)

    elif scenario == FraudReason.CARD_TESTING.value:
        # Many small transactions in rapid succession, on an
        # untrusted device/card, same merchant category repeated.
        if not _skip_marker():
            transaction["amount"] = round(random.uniform(1, 400), 2)
        if not _skip_marker():
            transaction["payment_method"] = PaymentMethod.CARD.value
        if not _skip_marker():
            transaction["sender_txn_count_24h"] = random.randint(25, 70)
        if not _skip_marker():
            transaction["velocity_score"] = round(random.uniform(0.70, 1.00), 3)
        if not _skip_marker():
            transaction["device_trusted"] = False

    elif scenario == FraudReason.MONEY_MULE.value:
        # Funds moved via bank transfer to a young, international
        # receiver account.
        if not _skip_marker():
            transaction["amount"] *= random.uniform(1.5, 4.0)
        if not _skip_marker():
            transaction["payment_method"] = PaymentMethod.BANK_TRANSFER.value
        if not _skip_marker():
            transaction["cross_border"] = True
            transaction["destination_country"] = random.choice(HIGH_RISK_COUNTRIES)
            transaction["high_risk_country"] = True
        if not _skip_marker():
            transaction["is_new_receiver"] = True
        if not _skip_marker():
            transaction["receiver_account_age_days"] = random.randint(1, 90)

    elif scenario == FraudReason.STOLEN_CARD.value:
        # Card-present-style spending spree on an untrusted device,
        # at night, on high-resale-value goods.
        if not _skip_marker():
            transaction["device_trusted"] = False
        if not _skip_marker():
            transaction["payment_method"] = PaymentMethod.CARD.value
        if not _skip_marker():
            transaction["merchant_category"] = random.choice([
                MerchantCategory.SHOPPING.value,
                MerchantCategory.TRAVEL.value,
                MerchantCategory.ELECTRONICS.value,
            ])
        if not _skip_marker():
            transaction["amount"] *= random.uniform(1.3, 3.0)
        if not _skip_marker():
            transaction["hour"] = random.randint(0, 6)

    elif scenario == FraudReason.SYNTHETIC_IDENTITY.value:
        # Freshly created sender and receiver accounts, ramped up
        # fast, usually via digital-first payment rails.
        if not _skip_marker():
            transaction["sender_account_age_days"] = random.randint(1, 45)
        if not _skip_marker():
            transaction["receiver_account_age_days"] = random.randint(1, 45)
        if not _skip_marker():
            transaction["amount"] *= random.uniform(1.5, 4.0)
        if not _skip_marker():
            transaction["sender_txn_count_24h"] = random.randint(20, 55)
        if not _skip_marker():
            transaction["payment_method"] = random.choice([
                PaymentMethod.UPI.value,
                PaymentMethod.WALLET.value,
            ])
        if not _skip_marker():
            transaction["velocity_score"] = round(random.uniform(0.60, 0.95), 3)

    return transaction


# ==========================================================
# Risk Scoring Engine
# ==========================================================

def sigmoid(x: float) -> float:
    """
    Convert a risk score into a probability.
    """

    return 1 / (1 + np.exp(-x))


def calculate_risk_score(
    transaction: Transaction,
) -> Tuple[int, List[str], Dict[str, int]]:
    """
    Calculate a weighted fraud risk score.

    Returns:
        risk_score (0-100, clipped)
        triggered_rules (list of rule names)
        risk_contributions (rule name -> score contribution, item 15)
    """

    contributions: Dict[str, int] = {}

    for reason, (weight, condition) in RISK_RULES.items():
        if condition(transaction):
            contributions[reason] = weight

    for reason, weight, condition in INTERACTION_RULES:
        if condition(transaction):
            contributions[reason] = weight

    raw_score = sum(contributions.values())
    score = min(raw_score, 100)

    reasons = list(contributions.keys())

    return score, reasons, contributions


def calculate_fraud_probability(risk_score: int) -> float:
    """
    Convert risk score into fraud probability.
    """

    normalized = (risk_score - 50) / 10

    probability = sigmoid(normalized)

    return round(float(probability), 4)


# ==========================================================
# Dataset Generator
# ==========================================================

def _iterate(n: int):
    if TQDM_AVAILABLE:
        return tqdm(range(n), desc="Generating transactions", unit="txn")
    return range(n)


def generate_dataset(num_transactions: int) -> pd.DataFrame:
    """
    Generate the complete synthetic dataset.
    """

    transactions = []

    fraud_count = 0
    legitimate_count = 0

    scenario_counts: Dict[str, int] = {}

    for i in _iterate(num_transactions):

        transaction = generate_transaction()

        transactions.append(transaction)

        if transaction["fraud_label"]:
            fraud_count += 1
        else:
            legitimate_count += 1

        scenario = transaction["fraud_reason"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1

        if not TQDM_AVAILABLE and (i + 1) % 10000 == 0:
            print(f"Generated {i + 1:,} transactions...")

    df = pd.DataFrame(transactions)

    # Difficulty engine: post-hoc label noise, applied once on the
    # full feature set. This must come after all features exist so
    # a flipped label is genuinely inconsistent with its row.
    df = apply_label_noise(df)

    print("\nGeneration Summary")
    print("-" * 50)
    print(f"Legitimate Transactions : {legitimate_count:,}")
    print(f"Fraud Transactions      : {fraud_count:,}")
    print(f"Fraud Rate (pre-noise)  : {(fraud_count / num_transactions) * 100:.2f}%")
    print(f"Fraud Rate (post-noise) : {df['fraud_label'].mean() * 100:.2f}%")
    print(f"Labels flipped          : {int(df['label_noise_applied'].sum())}")

    print("\nFraud Scenario Distribution (pre-noise)")
    print("-" * 50)
    for scenario, count in sorted(scenario_counts.items()):
        print(f"{scenario:<22}{count:>10,}")

    return df, scenario_counts


# ==========================================================
# Dataset Validation (item 17)
# ==========================================================

def validate_dataset(df: pd.DataFrame) -> None:
    """
    Perform sanity checks on the generated dataset. Fails fast
    (raises AssertionError) instead of silently printing stats
    for a broken dataset.
    """

    print("\nDataset Validation")
    print("-" * 50)

    non_list_cols = [
        c for c in df.columns
        if c not in ("risk_factors", "risk_contributions")
    ]

    missing = df[non_list_cols].isnull().sum().sum()
    duplicates = df[non_list_cols].duplicated().sum()
    fraud_rate = df["fraud_label"].mean() * 100

    print(f"Missing Values          : {missing}")
    print(f"Duplicate Rows          : {duplicates}")
    print(f"Fraud Rate              : {fraud_rate:.2f}%")
    print(f"Average Amount          : {df['amount'].mean():.2f}")
    print(f"Average Risk Score      : {df['risk_score'].mean():.2f}")
    print(f"Average Velocity Score  : {df['velocity_score'].mean():.2f}")

    assert df["fraud_label"].isin([0, 1]).all(), "fraud_label must be binary"
    assert df["risk_score"].between(0, 100).all(), "risk_score out of range"
    assert df["velocity_score"].between(0, 1).all(), "velocity_score out of range"
    assert (df["amount"] > 0).all(), "amount must be positive"
    assert missing == 0, f"dataset has {missing} missing values"

    print("\nAll validation checks passed.")

    print("\nAmount Statistics")
    print(df["amount"].describe())

    print("\nFraud Scenario Counts")
    print(df.groupby("fraud_reason")["fraud_label"].count().sort_values(ascending=False))

    print("\nRisk Score Distribution")
    print(df["risk_score"].describe())


# ==========================================================
# Train / Val / Test split (item 18)
# ==========================================================

def chronological_split(
    df: pd.DataFrame,
    train_frac: float = TRAIN_SPLIT,
    val_frac: float = VAL_SPLIT,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset chronologically (by timestamp) rather than
    randomly. This mirrors how a fraud model is actually deployed
    (train on the past, validate/test on the future) and avoids
    leaking future behaviour patterns into training.
    """

    ordered = df.sort_values("timestamp").reset_index(drop=True)

    n = len(ordered)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train_df = ordered.iloc[:train_end]
    val_df = ordered.iloc[train_end:val_end]
    test_df = ordered.iloc[val_end:]

    return train_df, val_df, test_df


# ==========================================================
# Main
# ==========================================================

def main() -> None:
    """
    Generate, validate and save the synthetic dataset.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Lynceus Synthetic Transaction Dataset Generator")
    print("=" * 70)
    print(f"Transactions        : {NUM_TRANSACTIONS:,}")
    print(f"Target Fraud        : {TARGET_FRAUD_RATE * 100:.2f}%")
    print(f"Mutation Skip Prob  : {FRAUD_MUTATION_SKIP_PROB}")
    print(f"Legit Lookalike Rate: {LEGIT_LOOKALIKE_RATE}")
    print(f"Feature Jitter Std  : {FEATURE_JITTER_STD}")
    print(f"Label Noise (F->L)  : {LABEL_NOISE_RATE_FRAUD_TO_LEGIT}")
    print(f"Label Noise (L->F)  : {LABEL_NOISE_RATE_LEGIT_TO_FRAUD}")
    print(f"Output Dir          : {OUTPUT_DIR}")
    print("=" * 70)

    print("\nGenerating dataset...\n")

    df, scenario_counts = generate_dataset(NUM_TRANSACTIONS)

    validate_dataset(df)

    # ------------------------------------------------------
    # Full Dataset (for analysis) - includes timestamp,
    # customer_profile, risk_contributions, everything.
    # ------------------------------------------------------

    full_dataset = OUTPUT_DIR / "transactions_full.csv"
    df.to_csv(full_dataset, index=False)

    # ------------------------------------------------------
    # ML Training Dataset
    #   - customer_profile EXCLUDED (item 2: latent variable,
    #     unknown at inference time)
    #   - fraud_probability EXCLUDED (item 4: leakage feature)
    #   - risk_score / risk_factors / risk_contributions EXCLUDED
    #     (derived directly from the same rules used to label risk;
    #     including them would hand the model the answer)
    #   - label_noise_applied EXCLUDED (would leak which rows were
    #     flipped, defeating the point of the noise)
    #   - timestamp KEPT (item 3): not used as a model feature,
    #     but needed for the chronological split below. Drop it
    #     right before fitting a model.
    # ------------------------------------------------------

    training_columns = [
        "timestamp",

        "amount",
        "currency",
        "payment_method",

        "hour",
        "day_of_week",
        "is_weekend",

        "sender_account_age_days",
        "receiver_account_age_days",

        "sender_txn_count_24h",
        "receiver_txn_count_24h",

        "sender_avg_amount_30d",
        "receiver_avg_amount_30d",

        "is_new_receiver",

        "origin_country",
        "destination_country",

        "merchant_category",

        "device_type",
        "device_trusted",

        "cross_border",
        "high_risk_country",

        "velocity_score",

        "fraud_label",
    ]

    training_df = df[training_columns].copy()

    training_dataset = OUTPUT_DIR / "transactions.csv"
    training_df.to_csv(training_dataset, index=False)

    # ------------------------------------------------------
    # Chronological train / val / test split
    # ------------------------------------------------------

    train_df, val_df, test_df = chronological_split(training_df)

    train_path = OUTPUT_DIR / "transactions_train.csv"
    val_path = OUTPUT_DIR / "transactions_val.csv"
    test_path = OUTPUT_DIR / "transactions_test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    # ------------------------------------------------------
    # Metadata (item 19)
    # ------------------------------------------------------

    metadata = {
        "generation_time": datetime.utcnow().isoformat() + "Z",
        "random_seed": RANDOM_SEED,
        "num_transactions": NUM_TRANSACTIONS,
        "target_fraud_rate": TARGET_FRAUD_RATE,
        "actual_fraud_rate": round(float(df["fraud_label"].mean()), 4),
        "fraud_scenario_counts": scenario_counts,
        "fraud_scenario_distribution_weights": FRAUD_SCENARIO_DISTRIBUTION,
        "difficulty_config": {
            "fraud_mutation_skip_prob": FRAUD_MUTATION_SKIP_PROB,
            "legit_lookalike_rate": LEGIT_LOOKALIKE_RATE,
            "feature_jitter_std": FEATURE_JITTER_STD,
            "label_noise_rate_fraud_to_legit": LABEL_NOISE_RATE_FRAUD_TO_LEGIT,
            "label_noise_rate_legit_to_fraud": LABEL_NOISE_RATE_LEGIT_TO_FRAUD,
        },
        "class_balance": {
            "legitimate": int((df["fraud_label"] == 0).sum()),
            "fraud": int((df["fraud_label"] == 1).sum()),
        },
        "split": {
            "train_rows": len(train_df),
            "val_rows": len(val_df),
            "test_rows": len(test_df),
            "method": "chronological (sorted by timestamp)",
            "fractions": {
                "train": TRAIN_SPLIT,
                "val": VAL_SPLIT,
                "test": TEST_SPLIT,
            },
        },
        "training_feature_names": [
            c for c in training_columns if c not in ("timestamp", "fraud_label")
        ],
        "files": {
            "full_dataset": str(full_dataset),
            "training_dataset": str(training_dataset),
            "train": str(train_path),
            "val": str(val_path),
            "test": str(test_path),
        },
    }

    metadata_path = OUTPUT_DIR / "dataset_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # ------------------------------------------------------
    # Schema (item 20)
    # ------------------------------------------------------

    schema = {
        "timestamp": {"dtype": "datetime", "role": "reference_only"},
        "amount": {"dtype": "float", "role": "feature"},
        "currency": {"dtype": "category", "role": "feature",
                     "values": [c.value for c in Currency]},
        "payment_method": {"dtype": "category", "role": "feature",
                            "values": [p.value for p in PaymentMethod]},
        "hour": {"dtype": "int", "role": "feature", "range": [0, 23]},
        "day_of_week": {"dtype": "int", "role": "feature", "range": [0, 6]},
        "is_weekend": {"dtype": "binary", "role": "feature"},
        "sender_account_age_days": {"dtype": "int", "role": "feature"},
        "receiver_account_age_days": {"dtype": "int", "role": "feature"},
        "sender_txn_count_24h": {"dtype": "int", "role": "feature"},
        "receiver_txn_count_24h": {"dtype": "int", "role": "feature"},
        "sender_avg_amount_30d": {"dtype": "float", "role": "feature"},
        "receiver_avg_amount_30d": {"dtype": "float", "role": "feature"},
        "is_new_receiver": {"dtype": "binary", "role": "feature"},
        "origin_country": {"dtype": "category", "role": "feature",
                            "values": COUNTRIES},
        "destination_country": {"dtype": "category", "role": "feature",
                                 "values": COUNTRIES + HIGH_RISK_COUNTRIES},
        "merchant_category": {"dtype": "category", "role": "feature",
                               "values": list(MERCHANTS.keys())},
        "device_type": {"dtype": "category", "role": "feature",
                         "values": DEVICE_TYPES},
        "device_trusted": {"dtype": "binary", "role": "feature"},
        "cross_border": {"dtype": "binary", "role": "feature"},
        "high_risk_country": {"dtype": "binary", "role": "feature"},
        "velocity_score": {"dtype": "float", "role": "feature", "range": [0, 1]},
        "fraud_label": {"dtype": "binary", "role": "target"},
    }

    schema_path = OUTPUT_DIR / "schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)

    print("\nDatasets Saved Successfully")
    print("-" * 50)
    print(f"Full Dataset     : {full_dataset}")
    print(f"Training Dataset : {training_dataset}")
    print(f"Train Split      : {train_path} ({len(train_df):,} rows)")
    print(f"Val Split        : {val_path} ({len(val_df):,} rows)")
    print(f"Test Split       : {test_path} ({len(test_df):,} rows)")
    print(f"Metadata         : {metadata_path}")
    print(f"Schema           : {schema_path}")

    print("\nTraining Features")
    print("-" * 50)
    for column in training_columns:
        print(column)

    print("\nSample Records")
    print("-" * 70)
    print(df.head())


if __name__ == "__main__":
    main()