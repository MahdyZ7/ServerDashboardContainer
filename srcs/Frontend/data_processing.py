# Data processing utilities for the Server Monitoring Dashboard
import pandas as pd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def safe_create_dataframe(data: List[Dict], name: str = "data") -> pd.DataFrame:
    """
    Safely create a DataFrame from data with error handling

    Args:
        data: List of dictionaries to convert
        name: Name of the data for logging

    Returns:
        DataFrame (empty if creation fails)
    """
    if not data:
        logger.warning(f"No {name} provided for DataFrame creation")
        return pd.DataFrame()

    if not isinstance(data, list):
        logger.error(f"{name} must be a list, got {type(data).__name__}")
        return pd.DataFrame()

    try:
        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with {len(df)} rows for {name}")
        return df
    except Exception as e:
        logger.error(f"Failed to create DataFrame for {name}: {e}")
        return pd.DataFrame()


def parse_dataframe_timestamps(
    df: pd.DataFrame, column: str = "timestamp"
) -> pd.DataFrame:
    """
    Safely parse timestamps in a DataFrame column

    Args:
        df: DataFrame containing timestamp column
        column: Name of the timestamp column

    Returns:
        DataFrame with parsed timestamps
    """
    if df.empty:
        return df

    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return df

    try:
        df[column] = pd.to_datetime(df[column], errors="coerce")

        # Count and log failed conversions
        failed_count = df[column].isna().sum()
        if failed_count > 0:
            logger.warning(
                f"Failed to parse {failed_count} timestamps in column '{column}'"
            )

        return df
    except Exception as e:
        logger.error(f"Error parsing timestamps in column '{column}': {e}")
        return df


def convert_numeric_columns(
    df: pd.DataFrame, columns: List[str], fillna: float = 0.0
) -> pd.DataFrame:
    """
    Safely convert specified columns to numeric types

    Args:
        df: DataFrame to process
        columns: List of column names to convert
        fillna: Value to fill NaN with after conversion

    Returns:
        DataFrame with numeric columns
    """
    if df.empty:
        return df

    for col in columns:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(fillna)
                logger.debug(f"Converted column '{col}' to numeric")
            except Exception as e:
                logger.error(f"Failed to convert column '{col}' to numeric: {e}")

    return df


def validate_dataframe_range(
    df: pd.DataFrame, column: str, min_val: float, max_val: float, clip: bool = False
) -> pd.DataFrame:
    """
    Validate that values in a DataFrame column are within range

    Args:
        df: DataFrame to validate
        column: Column name to check
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        clip: If True, clip values to range; if False, log warnings

    Returns:
        DataFrame (optionally with clipped values)
    """
    if df.empty or column not in df.columns:
        return df

    try:
        out_of_range = ((df[column] < min_val) | (df[column] > max_val)).sum()

        if out_of_range > 0:
            logger.warning(
                f"{out_of_range} values in column '{column}' are out of range "
                f"({min_val}-{max_val})"
            )

        if clip:
            df[column] = df[column].clip(lower=min_val, upper=max_val)
            logger.info(
                f"Clipped values in column '{column}' to range {min_val}-{max_val}"
            )

        return df
    except Exception as e:
        logger.error(f"Error validating range for column '{column}': {e}")
        return df


def prepare_historical_dataframe(
    historical_data: List[Dict], server_name: str
) -> pd.DataFrame:
    """
    Prepare historical data DataFrame with proper types and validation

    Args:
        historical_data: List of historical metric dictionaries
        server_name: Name of the server for logging

    Returns:
        Prepared DataFrame with validated data
    """
    df = safe_create_dataframe(historical_data, f"historical data for {server_name}")

    if df.empty:
        return df

    # Parse timestamps
    df = parse_dataframe_timestamps(df, "timestamp")

    # Convert numeric columns
    numeric_columns = [
        "cpu_load_1min",
        "cpu_load_5min",
        "cpu_load_15min",
        "ram_percentage",
        "disk_percentage",
        "logged_users",
        "tcp_connections",
    ]
    df = convert_numeric_columns(df, numeric_columns, fillna=0.0)

    # Validate ranges for percentage columns
    percentage_columns = ["ram_percentage", "disk_percentage"]
    for col in percentage_columns:
        if col in df.columns:
            df = validate_dataframe_range(df, col, 0, 100, clip=True)

    # Validate CPU load (typically 0-100 but can go higher)
    cpu_columns = ["cpu_load_1min", "cpu_load_5min", "cpu_load_15min"]
    for col in cpu_columns:
        if col in df.columns:
            df = validate_dataframe_range(df, col, 0, 1000, clip=False)

    # Sort by timestamp
    if "timestamp" in df.columns:
        try:
            df = df.sort_values("timestamp")
        except Exception as e:
            logger.warning(f"Failed to sort by timestamp: {e}")

    logger.info(f"Prepared historical DataFrame for {server_name} with {len(df)} rows")
    return df


def aggregate_metrics(
    metrics_list: List[Dict], operation: str = "mean"
) -> Dict[str, float]:
    """
    Aggregate metrics across multiple servers

    Args:
        metrics_list: List of server metrics dictionaries
        operation: Aggregation operation ('mean', 'sum', 'max', 'min')

    Returns:
        Dictionary of aggregated metrics
    """
    if not metrics_list:
        return {}

    try:
        df = safe_create_dataframe(metrics_list, "metrics for aggregation")
        if df.empty:
            return {}

        # Convert numeric columns
        numeric_columns = [
            "cpu_load_1min",
            "cpu_load_5min",
            "cpu_load_15min",
            "ram_percentage",
            "disk_percentage",
            "logged_users",
            "tcp_connections",
        ]
        df = convert_numeric_columns(df, numeric_columns)

        # Perform aggregation
        if operation == "mean":
            result = df[numeric_columns].mean().to_dict()
        elif operation == "sum":
            result = df[numeric_columns].sum().to_dict()
        elif operation == "max":
            result = df[numeric_columns].max().to_dict()
        elif operation == "min":
            result = df[numeric_columns].min().to_dict()
        else:
            logger.error(f"Unknown aggregation operation: {operation}")
            return {}

        logger.info(
            f"Aggregated metrics using {operation} across {len(metrics_list)} servers"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to aggregate metrics: {e}")
        return {}


def filter_recent_data(
    df: pd.DataFrame, timestamp_column: str = "timestamp", hours: int = 24
) -> pd.DataFrame:
    """
    Filter DataFrame to include only recent data

    Args:
        df: DataFrame to filter
        timestamp_column: Name of timestamp column
        hours: Number of hours to include

    Returns:
        Filtered DataFrame
    """
    if df.empty or timestamp_column not in df.columns:
        return df

    try:
        # Ensure timestamps are parsed
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_column]):
            df = parse_dataframe_timestamps(df, timestamp_column)

        # Calculate cutoff time
        cutoff_time = pd.Timestamp.now() - pd.Timedelta(hours=hours)

        # Filter data
        filtered_df = df[df[timestamp_column] >= cutoff_time]

        logger.info(
            f"Filtered data to last {hours} hours: {len(df)} -> {len(filtered_df)} rows"
        )

        return filtered_df

    except Exception as e:
        logger.error(f"Failed to filter recent data: {e}")
        return df


def calculate_trends(df: pd.DataFrame, column: str, window: int = 5) -> Optional[str]:
    """
    Calculate trend direction for a metric

    Args:
        df: DataFrame with time series data
        column: Column name to analyze
        window: Window size for moving average

    Returns:
        Trend direction: 'increasing', 'decreasing', or 'stable'
    """
    if df.empty or column not in df.columns or len(df) < window:
        return None

    try:
        # Calculate moving average
        ma = df[column].rolling(window=window).mean()

        if ma.isna().all():
            return None

        # Compare first and last values of moving average
        first_val = ma.dropna().iloc[0]
        last_val = ma.dropna().iloc[-1]

        change_percent = (
            ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
        )

        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"

    except Exception as e:
        logger.error(f"Failed to calculate trends for column '{column}': {e}")
        return None


def detect_anomalies(
    df: pd.DataFrame, column: str, threshold_std: float = 3.0
) -> pd.Series:
    """
    Detect anomalies in a metric using standard deviation

    Args:
        df: DataFrame with metric data
        column: Column name to analyze
        threshold_std: Number of standard deviations for anomaly threshold

    Returns:
        Boolean Series indicating anomalies
    """
    if df.empty or column not in df.columns:
        return pd.Series(dtype=bool)

    try:
        mean = df[column].mean()
        std = df[column].std()

        if pd.isna(std) or std == 0:
            return pd.Series([False] * len(df))

        anomalies = (df[column] - mean).abs() > (threshold_std * std)

        anomaly_count = anomalies.sum()
        if anomaly_count > 0:
            logger.info(f"Detected {anomaly_count} anomalies in column '{column}'")

        return anomalies

    except Exception as e:
        logger.error(f"Failed to detect anomalies for column '{column}': {e}")
        return pd.Series([False] * len(df))
