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
    population_ack_signature: str | None = None

def invalidate_after_change(state):
    state.population_ack_signature=None;state.artifacts=None;state.reviewed=False;state.download_key=None
    return state
