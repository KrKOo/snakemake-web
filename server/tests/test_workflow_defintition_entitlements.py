import pytest
from uuid import uuid4

from app import create_app
from app.workflow_definition import Entitlement, WorkflowDefinitionMetadata


@pytest.fixture
def app():
    app = create_app()

    yield app


@pytest.fixture
def entitlements() -> list[Entitlement]:
    res: list[Entitlement] = [
        {
            "prefix": r"urn:geant:lifescience-ri\.eu:",
            "values": [r".*:entitled:.*", r".*:students:.*"],
            "suffix": r".*",
        },
        {
            "prefix": r"urn:swamid:.*",
            "values": [r"members:organization:EGI"],
            "suffix": r":#swamid.se",
        },
    ]

    return res


@pytest.fixture
def workflow_definition(app, entitlements):
    return WorkflowDefinitionMetadata(
        dir="dir", id=uuid4(), name="name", allowed_entitlements=entitlements
    )


def test_get_allowed_entitlement_patterns(app, workflow_definition, entitlements):
    expected = [
        r"^urn:geant:lifescience-ri\.eu:(.*:entitled:.*|.*:students:.*).*$",
        r"^urn:swamid:.*(members:organization:EGI):#swamid.se$",
    ]

    assert workflow_definition.allowed_entitlement_patterns == expected
