import re
from uuid import UUID
from typing import TypedDict
from pydantic import BaseModel


class Entitlement(TypedDict):
    prefix: str
    values: list[str]
    suffix: str


class WorkflowDefinitionMetadata(BaseModel):
    dir: str
    id: UUID
    name: str
    allowed_entitlements: list[Entitlement] | None = None

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
