from dataclasses import dataclass

@dataclass
class ScanRun:
    scan_id:str
    organization_id:str
    status:str

@dataclass
class ScanResult:
    scan_id:str
    login_session_external_id:str
    risk_score:int
    case_id:str|None=None
