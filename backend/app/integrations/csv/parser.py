import pandas as pd
from io import StringIO
from typing import List, Dict, Any

def parse_csv_contents(contents: bytes) -> List[Dict[str, Any]]:
    """Parse CSV bytes into a list of row dictionaries.
    Returns a list of dictionaries where keys are column headers.
    """
    df = pd.read_csv(StringIO(contents.decode("utf-8")))
    return df.to_dict(orient="records")
