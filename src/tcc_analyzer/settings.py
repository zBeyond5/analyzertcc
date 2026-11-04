from dataclasses import dataclass, field
from .models import ImportLimits

@dataclass(frozen=True)
class Settings:
    import_limits: ImportLimits = field(default_factory=ImportLimits)
    max_heavy_runs: int = 2
    retention_minutes: int = 60
    cleanup_interval_seconds: int = 300
    max_artifact_bytes: int = 64*1024**2
