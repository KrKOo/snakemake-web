import re
from uuid import UUID
from typing import Dict, Optional, TypedDict
from pydantic import BaseModel


class Entitlement(TypedDict):
    prefix: str
    values: list[str]
    suffix: str


class WorkflowDefinitionMetadata(BaseModel):
    dir: str
    id: UUID
    name: str
    allowed_entitlements: Optional[list[Entitlement]] = None
    input_mapping: Optional[Dict[str, str]] = None

    @property
    def allowed_entitlement_patterns(self) -> list[str]:
        if not self.allowed_entitlements:
            return []

        patterns = []

        for entitlement in self.allowed_entitlements:
            pattern = f'^{entitlement["prefix"]}({"|".join(entitlement["values"])}){entitlement["suffix"]}$'
            patterns.append(pattern)

        return patterns

    def __repr__(self):
        return f"WorkflowDefinition({self.dir}, {self.id}, {self.name}, {self.allowed_entitlement_patterns})"

    def is_entitlement_satisfied(self, entitlements: list[str]) -> bool:
        for pattern in self.allowed_entitlement_patterns:
            if any(re.match(pattern, e) for e in entitlements):
                return True

        return False
    
    def get_input_mapping(self, params: Dict[str, str]) -> Dict[str, str]:
        if not self.input_mapping:
            return {}
        
        input_mapping = {}
        for key, value in self.input_mapping.items():
            input_mapping[key] = value.format(**params)
        
        return input_mapping
