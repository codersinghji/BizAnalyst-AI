

import pandas as pd


def load_dataset(file):

    filename = file.name.lower()

    if filename.endswith(".csv"):

        # Try common CSV encodings
        encodings = ["utf-8-sig", "cp1252", "latin1"]

        df = None

        for encoding in encodings:
            try:
                file.seek(0)

                df = pd.read_csv(
                    file,
                    encoding=encoding
                )

                break

            except UnicodeDecodeError:
                continue

        if df is None:
            raise ValueError(
                "Unable to decode CSV. Please check file encoding."
            )

    elif filename.endswith((".xlsx", ".xls")):

        df = pd.read_excel(file)

    else:
        raise ValueError("Unsupported file format")

    if df.empty:
        raise ValueError("Uploaded dataset is empty")

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


def validate_dataset(df):

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "missing_values": int(df.isnull().sum().sum()),
        "column_names": df.columns.tolist()
    }
