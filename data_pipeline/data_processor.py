# data_processor.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def remove_duplicates(df):
    """Remove duplicate rows."""
    rows_before = len(df)
    df = df.drop_duplicates()
    logger.debug(f"remove_duplicates: {rows_before} → {len(df)} rows")
    return df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis not in ("rows", "columns"):
        logger.error(f"Unsupported missing axis: {axis}")
        raise ValueError(f"Unsupported missing axis: {axis}")

    if axis == "rows":
        rows_before = len(df)
        df = df.dropna(axis=0)
        logger.debug(f"handle_missing: {rows_before} → {len(df)} rows")
    else:
        columns_before = len(df.columns)
        df = df.dropna(axis=1)
        logger.debug(f"handle_missing: {columns_before} → {len(df.columns)} columns")

    return df


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ("iqr", "zscore"):
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    for column in columns:
        if column not in df.columns:
            logger.warning(f"Column not found: {column}")
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            logger.warning(f"Column is not numeric: {column}")
            continue

        if method == "iqr":
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            spread = q3 - q1
            lower = q1 - threshold * spread
            upper = q3 + threshold * spread
        else:
            mean = df[column].mean()
            std = df[column].std()
            if pd.isna(std) or std == 0:
                logger.warning(f"Column has no spread, skipping: {column}")
                continue
            lower = mean - threshold * std
            upper = mean + threshold * std

        rows_before = len(df)
        df = df[(df[column] >= lower) & (df[column] <= upper)]
        logger.debug(
            f"{column}: method={method}, threshold={threshold}, "
            f"lower={lower}, upper={upper}, removed={rows_before - len(df)}"
        )

    return df


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    processing = config.get("processing", {})

    if processing.get("remove_duplicates"):
        df = remove_duplicates(df)

    missing = processing.get("missing", {})
    if missing.get("enabled"):
        df = handle_missing(df, axis=missing.get("axis", "rows"))

    outliers = processing.get("outliers", {})
    if outliers.get("enabled"):
        df = remove_outliers(
            df,
            columns=outliers.get("columns", []),
            method=outliers.get("method"),
            threshold=outliers.get("threshold"),
        )

    return df


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    rows_before = len(df_before)
    rows_after = len(df_after)
    columns_before = len(df_before.columns)
    columns_after = len(df_after.columns)

    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "columns_removed": columns_before - columns_after,
    }
