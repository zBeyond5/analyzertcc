from dataclasses import dataclass, field
from typing import Any
import pandas as pd

class DomainError(ValueError):
    def __init__(self, code, message_pt=None):
        self.code = code
        super().__init__(message_pt or code)

@dataclass(frozen=True)
class ImportLimits:
    max_bytes: int = 20*1024**2
    max_rows: int = 100000
    max_columns: int = 500
    max_unpacked_bytes: int = 128*1024**2
    max_zip_entries: int = 2000

@dataclass(frozen=True)
class CsvOptions:
    encoding: str = 'utf-8-sig'
    separator: str = ';'
    decimal: str = ','

@dataclass(frozen=True)
class DatasetMeta:
    row_count: int
    column_count: int
    columns: tuple[str, ...]
    source_sha256: str

@dataclass
class ImportedDataset:
    raw: pd.DataFrame
    meta: DatasetMeta
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class VariableSpec:
    name: str
    label: str
    kind: str
    allowed_values: tuple | None = None
    missing_values: tuple = ('',)
    export_default: bool = True
    mapping_status: str = 'pending'
    labels: dict = field(default_factory=dict)

@dataclass(frozen=True)
class ResearchProfile:
    id: str
    version: str
    variables: tuple[VariableSpec, ...]
    psqi_rules: dict = field(default_factory=lambda: {'status':'pending'})
    derived_rules: dict = field(default_factory=dict)
    comparisons: tuple = ()
    confirmation: str = ''
    input_fields: tuple = ()
    derived_fields: tuple = ()
    instrument_mode: str = 'recorded'
    canonical_codes: dict = field(default_factory=dict)

@dataclass(frozen=True)
class ValidationIssue:
    row_index: int | None
    variable: str
    raw_value: Any
    code: str
    severity: str
    message_pt: str

@dataclass
class ValidationReport:
    issues: tuple[ValidationIssue, ...]
    @property
    def blocks_analysis(self):
        return any(i.severity=='error' for i in self.issues)

@dataclass(frozen=True)
class Transformation:
    row_index: int | None
    field: str
    before: Any
    after: Any
    reason: str

@dataclass
class PreparedDataset:
    data: pd.DataFrame
    source_meta: DatasetMeta
    transformations: tuple[Transformation, ...]
    validation: ValidationReport

@dataclass(frozen=True)
class ScoreResult:
    total: int | None
    category: int | None
    components: tuple = ()
    issues: tuple[str, ...] = ()

@dataclass(frozen=True)
class ComparisonSpec:
    id: str
    outcome: str
    predictor: str
    family: str = 'exploratory'
    method: str = 'auto'
    rationale: str = 'Comparação associativa, sem interpretação causal.'
    group_order: tuple = ()
    event_value: Any = None

@dataclass
class EffectEstimate:
    value: float | None
    ci95: tuple[float,float] | None = None
    method: str = ''
    unavailable_reason: str | None = None

@dataclass
class TestResult:
    method: str
    n_effective: int
    n_missing: int = 0
    statistic: float | None = None
    p_value: float | None = None
    p_kind: str = 'not_computed'
    effects: dict[str, EffectEstimate] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    seed: int | None = None

@dataclass
class AnalysisResult:
    spec: ComparisonSpec
    result: TestResult

@dataclass
class SummaryResult:
    field: str
    n_total: int
    n_valid: int
    n_missing: int
    metrics: dict
    counts: dict
    denominator: str = 'Respostas válidas da variável'

@dataclass(frozen=True)
class CsvFormat:
    encoding: str = 'utf-8-sig'
    separator: str = ';'
    decimal: str = ','

@dataclass
class ExportManifest:
    files: dict
    sha256: dict = field(default_factory=dict)
    csv_format: CsvFormat = field(default_factory=CsvFormat)
    excluded_fields: tuple = ()
    text_escapes: tuple = ()

@dataclass
class ReportTables:
    descriptive: tuple
    bivariate: tuple
    notes: tuple
    narrative: tuple

@dataclass
class RunArtifacts:
    files: dict
    tables: ReportTables
    results: tuple
    metadata: dict

@dataclass
class AnalysisPopulation:
    data: pd.DataFrame
    included_rows: tuple
    excluded: tuple
    policy: str
