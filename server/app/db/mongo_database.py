from typing import Type, TypeVar
from pymongo.database import Database

from .base_database import BaseDatabase
from .models import Model

ModelT = TypeVar("ModelT", bound=Model)
class MongoDatabase(BaseDatabase):
    def __init__(self, db: Database):
        self.db = db

    def get_one(self, model: Type[ModelT], filter: dict) -> ModelT | None:
        filter = self._translate_filter_keys(model, filter)
        result = self.db[model._collection_name].find_one(filter)

        if result is None:
            return None
        
        return model.model_validate(result)

    def get_many(self, model: Type[ModelT], filter: dict) -> list[ModelT]:
        filter = self._translate_filter_keys(model, filter)
        result = self.db[model._collection_name].find(filter)
        return [model.model_validate(r) for r in result]

    def insert_one(self, model: Type[ModelT], data: ModelT) -> ModelT:
        insert_result = self.db[model._collection_name].insert_one(data.model_dump(by_alias=True))
        result = self.db[model._collection_name].find_one({"_id": insert_result.inserted_id})
        return model.model_validate(result)

    def delete_one(self, model: Type[ModelT], filter: dict):
        filter = self._translate_filter_keys(model, filter)
        self.db[model._collection_name].delete_one(filter)

    def update_one(self, model: Type[ModelT], filter: dict, data: ModelT) -> ModelT:
        filter = self._translate_filter_keys(model, filter)
        self.db[model._collection_name].update_one(filter, {"$set": data.model_dump(by_alias=True)})
        result = self.db[model._collection_name].find_one(filter)
        return model.model_validate(result)

    def _translate_filter_keys(self, model: Type[ModelT], filter: dict) -> dict:
        """
        Translates filter keys from model field names to database field names (aliases)
        if an alias is defined for that field in the Pydantic model.
        """
        db_filter = {}
        model_fields = model.model_fields

        for key, value in filter.items():
            field_info = model_fields.get(key)
            if field_info and field_info.alias:
                db_filter[field_info.alias] = value
            else:
                db_filter[key] = value
        return db_filter