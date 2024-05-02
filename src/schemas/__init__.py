from pydantic import BaseModel
import abc


class Schema(BaseModel, abc.ABC):
    @abc.abstractmethod
    def wrap_result(row: tuple):
        pass


def wrap_result_with_schema(row: tuple, cls):
    columns = cls.schema()["properties"].keys()
    values = list(row)

    cls_dict = {col: val for (col, val) in zip(columns, values)}

    return cls(**cls_dict)
