from abc import ABC, abstractmethod
from typing import Type, TypeVar

from .models import Model

ModelT = TypeVar("ModelT", bound=Model)
class BaseDatabase(ABC):
    @abstractmethod
    def get_one(self, model: Type[ModelT], filter: dict) -> ModelT | None:
        raise NotImplementedError
    
    @abstractmethod
    def get_many(self, model: Type[ModelT], filter: dict) -> list[ModelT]:
        raise NotImplementedError

    @abstractmethod
    def insert_one(self, model: Type[ModelT], data: ModelT) -> ModelT:
        raise NotImplementedError

    @abstractmethod
    def delete_one(self, model: Type[ModelT], filter: dict):
        raise NotImplementedError

    @abstractmethod
    def update_one(self, model: Type[ModelT], filter: dict, data: ModelT) -> ModelT:
        raise NotImplementedError


