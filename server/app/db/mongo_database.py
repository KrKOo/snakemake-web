from typing import Type, TypeVar
from pymongo.database import Database

from .base_database import BaseDatabase
from .models import Model

ModelT = TypeVar("ModelT", bound=Model)
class MongoDatabase(BaseDatabase):
    def __init__(self, db: Database):
        self.db = db

    def get_one(self, model: Type[ModelT], filter: dict) -> ModelT | None:
        result = self.db[model._collection_name].find_one(filter)

        if result is None:
            return None
        
        return model.model_validate(result)

    def get_many(self, model: Type[ModelT], filter: dict) -> list[ModelT]:
        result = self.db[model._collection_name].find(filter)
        return [model.model_validate(r) for r in result]

    def insert_one(self, model: Type[ModelT], data: ModelT) -> ModelT:
        insert_result = self.db[model._collection_name].insert_one(data.model_dump(by_alias=True))
        result = self.db[model._collection_name].find_one({"_id": insert_result.inserted_id})
        return model.model_validate(result)

    def delete_one(self, model: Type[ModelT], filter: dict):
        self.db[model._collection_name].delete_one(filter)

    def update_one(self, model: Type[ModelT], filter: dict, data: ModelT) -> ModelT:
        self.db[model._collection_name].update_one(filter, {"$set": data.model_dump(by_alias=True)})
        result = self.db[model._collection_name].find_one(filter)
        return model.model_validate(result)
