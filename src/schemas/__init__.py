from pydantic import BaseModel
import abc


class Schema(BaseModel, abc.ABC):
    def keys_as_str(self) -> str:
        obj_dict: dict = self.dict()
        keys: list[str] = list(obj_dict.keys())

        keys_str: str = f"{keys[0]}"
        for key in keys[1:]:
            keys_str += f", {key}"

        return keys_str

    def as_tuple_value_str(self) -> str:
        obj_dict: dict = self.dict()
        # keys: list[str] = list(obj_dict.keys())
        vals = list(obj_dict.values())

        # for exclude_key in exclude_keys:
        #     if exclude_key in keys:
        #         rm_idx = keys.index(exclude_key)
        #         keys.pop(rm_idx)
        #         vals.pop(rm_idx)

        val_0 = vals[0]
        tuple_str: str = f"'{val_0}'" if type(val_0) is str else f"{val_0}"
        for val in vals[1:]:
            if type(val) is str:
                tuple_str += f", '{val}'"
            else:
                tuple_str += f", {val}"

        return f"({tuple_str})"

    @abc.abstractmethod
    def wrap_result(row: tuple):
        pass


def wrap_result_with_schema(row: tuple, cls):
    columns = list(cls.schema()["properties"].keys())
    values = list(row)

    cls_dict = {col: val for (col, val) in zip(columns, values)}

    return cls(**cls_dict)
