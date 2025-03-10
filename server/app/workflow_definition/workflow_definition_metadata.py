import re
from typing import TypedDict


class Entitlement(TypedDict):
    prefix: str
    values: list[str]
    suffix: str


class WorkflowDefinitionMetadata:
    def __init__(
        self,
        dir: str,
        id: str,
        name: str,
        allowed_entitlements: list[Entitlement],
    ):
        self.dir = dir
        self.id = id
        self.name = name
        self.allowed_entitlements = allowed_entitlements
        self.allowed_entitlement_patterns = self._get_allowed_entitlement_patterns(
            allowed_entitlements
        )

    def __repr__(self):
        return f"WorkflowDefinition({self.dir}, {self.id}, {self.name}, {self.allowed_entitlement_patterns})"

    def _get_allowed_entitlement_patterns(
        self, allowed_entitlements: list[Entitlement]
    ) -> list[str]:
        if not allowed_entitlements:
            return []

        patterns = []

        for entitlement in allowed_entitlements:
            pattern = f'^{entitlement["prefix"]}({"|".join(entitlement["values"])}){entitlement["suffix"]}$'
            patterns.append(pattern)

        return patterns

    def is_entitlement_satisfied(self, entitlements: list[str]) -> bool:
        for pattern in self.allowed_entitlement_patterns:
            if any(re.match(pattern, e) for e in entitlements):
                return True

        return False
