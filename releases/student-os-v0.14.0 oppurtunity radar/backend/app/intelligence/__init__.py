"""The learning core: feature engineering + a trainable ranker.

The rule-based prioritizer stays as the baseline and cold-start fallback; the
learned ranker here is trained on labeled data and compared against it.
"""
