from dataclasses import dataclass, field
import datetime as dt

def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

@dataclass
class Evidence:
    """Provenance record attached to every displayed indicator."""
    indicator: str
    value: object
    unit: str
    geography: str
    valid_time: str
    source: str
    method: str
    classification: str          # Observation | Forecast | Model estimate | Official bulletin | Sample data
    quality: str = "OK"
    limitations: str = ""
    retrieved: str = field(default_factory=now_utc)
