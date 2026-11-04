from dataclasses import dataclass,field
from ..jobs import SessionContext

@dataclass
class WorkflowState:
    session: SessionContext = field(default_factory=SessionContext)
    job: object = None
    imported: object = None
    prepared: object = None
    profile: object = None
    options: object = None
    artifacts: object = None
    fictitious: bool = False
    reviewed: bool = False
    download_key: str | None = None
    csv_options: object = None

def invalidate_after_change(state):
    state.artifacts=None;state.reviewed=False;state.download_key=None
    return state
