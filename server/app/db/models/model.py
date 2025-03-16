from typing import ClassVar
from pydantic import BaseModel

class Model(BaseModel):
    _collection_name: ClassVar[str]  # Subclasses must define this

    def __new__(cls, *args, **kwargs):
        """Ensures subclasses define '_collection_name' before instantiation."""
        if "_collection_name" not in cls.__dict__ or not isinstance(cls.__dict__["_collection_name"], str):
            raise TypeError(f"{cls.__name__} must define a '_collection_name' string attribute.")
        return super().__new__(cls)