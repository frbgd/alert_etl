from enum import Enum
from typing import List, Optional


class TargetGroup(Enum):
    first_line = 'L1'
    second_line = 'L2'
    test = 'LPageTest'


class Status(Enum):
    empty = -1
    no_import = 0
    prod = 1
    pilot = 2


class Alert:
    source: str
    source_ref: str
    use_case: str
    information_system: str
    information_system_status: Status = Status.empty
    priority: str = ''
    use_case_title: str = ''
    use_case_status: Status = Status.empty
    playbook_links: str = ''
    incident_category: str = ''
    target_group: TargetGroup = TargetGroup.test
    closing_reason: str = 'Closed by the IRP Integration'
    raw_data: dict
    data: dict
    source_ips: Optional[List[str]] = None
    destination_ips: Optional[List[str]] = None
    log_examples: Optional[List[str]] = None

    def __init__(
            self,
            source: str,
            raw_data: dict,
            source_ref: str,
            use_case: str = '',
            information_system: str = ''
    ):
        self.source = source
        self.use_case = use_case
        self.information_system = information_system
        self.raw_data = raw_data
        self.source_ref = source_ref

    def __repr__(self):
        return f'Alert sourceRef:{self.source_ref} IS:{self.information_system} UC:{self.use_case} ' \
               f'target:{self.target_group.value}'


class ETLData:
    relevant: List[Alert]
    imported: List[Alert]
    irrelevant: List[Alert]

    def __init__(self):
        self.relevant = []
        self.imported = []
        self.irrelevant = []

    def __repr__(self):
        return f'ETLData ' \
               f'relevant:{len(self.relevant)} ' \
               f'imported:{len(self.imported)} ' \
               f'irrelevant:{len(self.irrelevant)}'

    def __len__(self):
        return len(self.irrelevant) + len(self.imported) + len(self.relevant)
