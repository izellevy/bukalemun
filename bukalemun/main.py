from pprint import pprint
from typing import Type, Dict, List, Set, Optional

from bidict import bidict
from pydantic import BaseModel


class Property(BaseModel):
    id: Optional[str]
    name: str
    type: str
    model_name: str

    def __eq__(self, other):
        return self.name == other.name and \
               self.type == other.type and \
               self.model_name == other.model_name

    def __repr__(self):
        return f"{self.model_name} -> {self.name}: {self.type} ({self.id})"

    def __hash__(self):
        return hash(f'{self.name}-{self.type}-{self.model_name}')


class Path(object):
    def __init__(self, namespace):
        self.namespace = namespace

    def __repr__(self):
        return f'*{self.namespace}'


class PropertyPool(object):

    def __init__(self, prop_list: List[Property] = None):
        self.pool = bidict()
        self.models = []
        self.props = []
        self.types = []

        if prop_list is not None:
            self.add(prop_list)


    def get_create_index(self, l: List, elem):
        if elem in l:
            return l.index(elem)
        else:
            length = len(l)
            l.append(elem)
            return length

    def add(self, props: List[Property]):
        added_props = []
        for prop in props:
            if prop not in self.pool:
                model_idx = self.get_create_index(self.models, prop.model_name)
                prop_idx = self.get_create_index(self.props, prop.name)
                type_idx = self.get_create_index(self.types, prop.type)
                prop.id = f"{model_idx}-{prop_idx}-{type_idx}"
                self.pool[prop] = prop.id
                added_props.append(prop)

        return added_props

    def get_not_mapped(self, props, mapping: Dict[str, Path]):
        merged_mapping = self.merged_mapping(props, mapping)
        resolved = set(merged_mapping.keys())
        not_mapped = set(self.pool.values()).difference(resolved)
        inv_map = self.pool.inverse
        prop_not_mapped = set(inv_map[elem] for elem in not_mapped)
        return prop_not_mapped

    def get_auto_mapped(self, props) -> Set[str]:
        auto_mapped = set()
        for prop in props:
            if prop in self.pool:
                val = self.pool[prop]
                auto_mapped.add(val)
        return auto_mapped

    def validate_mapping(self, mapping: Dict[str, Path]):
        for prev, nxt in mapping.items():
            inv_map = self.pool.inverse
            assert inv_map[prev].model_name == inv_map[nxt].model_name

    def merged_mapping(self, props, mapping: Dict[str, Path] = None):

        auto_mapped = self.get_auto_mapped(props)

        d = {val: Path(str(val)) for val in auto_mapped}

        if mapping is not None:
            d.update(mapping)
        return d

    def clone(self):
        prop_list = list(self.pool.keys())
        return PropertyPool(prop_list)


class IndexBuilder(object):
    def __init__(self):
        self.property_pool: PropertyPool = PropertyPool()
        self.index: Dict[str, Dict[str, Path]] = {}
    #
    # def convert_index(self):
    #     d = {}
    #     for version, mapping in self.index.items():
    #         p = {}
    #         for key, path in mapping.items():
    #             pass

    def find_missing(self, models: List[Type[BaseModel]], mapping: Dict[str, Path] = None):
        props = self.models_to_props(models)
        property_pool = self.property_pool.clone()
        added_props = property_pool.add(props)
        not_mapped = property_pool.get_not_mapped(props, mapping)
        not_mapped_with_suggested = {
        }
        for not_mapped_prop in not_mapped:
            not_mapped_with_suggested[not_mapped_prop] = {
                'suggested': {prop for prop in added_props if prop.model_name == not_mapped_prop.model_name}}
        return {'not_mapped': not_mapped_with_suggested, 'all_added': set(added_props),
                'all': list(property_pool.pool.keys())}

    def add(self, version, models: List[Type[BaseModel]], mapping: Dict[str, Path] = None):
        props = self.models_to_props(models)

        self.property_pool.add(props)

        prop_not_mapped = self.property_pool.get_not_mapped(props, mapping)

        if prop_not_mapped:
            raise Exception(f'Not mapped {prop_not_mapped}')

        self.index[version] = self.property_pool.merged_mapping(props, mapping)

    def model_to_props(self, model: Type[BaseModel]):
        return [Property(name=field_name, type=field.type_.__name__, model_name=model.__name__) for field_name, field in
                model.__fields__.items()]

    @classmethod
    def field_to_prop(cls, model, field_name):
        field = model.__fields__[field_name]
        return Property(name=field_name, type=field.type_.__name__, model_name=model.__name__)

    def models_to_props(self, models: List[Type[BaseModel]]):
        props = []
        for model in models:
            props += self.model_to_props(model)
        return props


def main():
    index_builder = IndexBuilder()

    # NEW INDEX
    # Entities: Person (0), Root (1), Salary (2), Human (3)
    # props: name (0), surname (1), age (2), person (3), last_name (4), salary (5), amount (6), currency (7), total_amount (8), human (9)
    # Types: str (0), int (1), Person (2), Salary (3), Human (4)

    # GLOBAL INDEX
    # name:str (Person) - 1 (0-0-0)
    # surname:str (Person) - 2 (0-1-0)
    # age:int (Person) - 3 (0-2-1)
    # person: Person (Root) - 4 (1-3-2)
    # last_name:str (Person) - 5 (0-4-0)
    # salary: int (Person) - 6 (0-5-1)
    # salary: Salary (Person) - 7 (0-5-3)
    # amount: int (Salary) - 8 (2-6-1)
    # currency: str (Salary) - 9 (2-7-0)
    # total_amount: int (Salary) - 10 (2-8-1)
    # human: Human (Root) - 11 (1-9-4)
    # name:str (Human) - 12 (3-0-0)
    # surname:str (Human) - 13 (3-1-0)
    # age:int (Human) - 14 (3-2-1)
    # salary: Salary (Human) - 15 (3-5-3)

    # Index (v1)
    # 1 (0-0-0)
    # 2 (0-1-0)
    # 3 (0-2-1)
    # 4 (1-3-2)

    def v1():
        """Init"""

        class Person(BaseModel): #0
            name: str
            surname: str
            age: int

        class Root(BaseModel): #1
            person: Person

        return [Person, Root]

    index_builder.add('v1', v1())

    # pprint(index_builder.property_pool)
    pprint(index_builder.index)
    # pprint(index_builder.counter)

    # Index (v2)
    # 1 (0-0-0)
    # 3 (0-2-1)
    # 4 (1-3-2)
    # 5 (0-4-0)
    # ----
    # 2 (0-1-0) -> 5 (0-4-0)

    def v2():
        """Change surname to last_name"""

        class Person(BaseModel):  #0
            name: str
            last_name: str
            age: int

        class Root(BaseModel):  #1
            person: Person

        return [Person, Root]

    index_builder.add('v2', v2(), {"0-1-0": Path('0-4-0')})

    # pprint(index_builder.property_pool.pool)
    # pprint(index_builder.index)
    # pprint(index_builder.property_pool.counter)

    # Index (v3)
    # 1 (0-0-0)
    # 2 (0-1-0)
    # 3 (0-2-1)
    # 4 (1-3-2)
    # ----
    # 5 (0-4-0) -> 2 (0-1-0)

    def v3():
        class Person(BaseModel):
            """Change last_name to surname"""
            name: str
            surname: str
            age: int

        class Root(BaseModel):
            person: Person

        return [Person, Root]

    index_builder.add('v3', v3(), {'0-4-0': Path('0-1-0')})

    # pprint(index_builder.property_pool.pool)
    # pprint(index_builder.index)
    # pprint(index_builder.property_pool.counter)

    # Index (v4)
    # 1 (0-0-0)
    # 2 (0-1-0)
    # 3 (0-2-1)
    # 4 (1-3-2)
    # 6 (0-5-1)
    # ----
    # 5 (0-4-0) -> 2 (0-1-0)

    def v4():
        class Person(BaseModel):
            """Add salary"""
            name: str
            surname: str
            age: int
            salary: int

        class Root(BaseModel):
            person: Person

        return [Person, Root]

    index_builder.add('v4', v4(), {'0-4-0': Path('0-1-0')})

    # Index (v5)
    # 1 (0-0-0)
    # 2 (0-1-0)
    # 3 (0-2-1)
    # 4 (1-3-2)
    # 7 (0-5-3)
    # 8 (2-6-1)
    # 9 (2-7-0)
    # ----
    # 5 (0-4-0) -> 2 (0-1-0)
    # 6 (0-5-1) -> 7.8 (0-5-3.2-6-1)

    def v5():
        class Salary(BaseModel):
            amount: int
            currency: str

        class Person(BaseModel):
            """Change to salary object"""
            name: str
            surname: str
            age: int
            salary: Salary

        class Root(BaseModel):
            person: Person

        return [Root, Person, Salary]

    index_builder.add('v5', v5(), {"0-4-0": "0-1-0", "0-5-1": Path('0-5-3.2-6-1')})

    # pprint(index_builder.property_pool.pool)
    # pprint(index_builder.index)

    # pprint(index_builder.property_pool.counter)

    # Index (v6)
    # 1 (0-0-0)
    # 2 (0-1-0)
    # 3 (0-2-1)
    # 4 (1-3-2)
    # 7 (0-5-3)
    # 9 (2-7-0)
    # 10 (2-8-1)
    # ----
    # 5 (0-4-0) -> 2 (0-1-0)
    # 6 (0-5-1) -> 7.10 (0-5-3.2-8-1)
    # 8 (2-6-1) -> 10 (2-8-1)

    def v6():
        class Salary(BaseModel):
            """Change to total_amount"""
            total_amount: int
            currency: str

        class Person(BaseModel):
            name: str
            surname: str
            age: int
            salary: Salary

        class Root(BaseModel):
            person: Person

        return [Root, Person, Salary]

    index_builder.add('v6', v6(), {"0-4-0": Path('0-1-0'), "0-5-1": Path('0-5-3.2-8-1'), "2-6-1": Path('2-8-1')})



    # Index (v7)
    # 9 (2-7-0)
    # 10 (2-8-1)
    # 11 (1-9-4)
    # 12 (3-0-0)
    # 13 (3-1-0)
    # 14 (3-2-1)
    # 15 (3-5-3)
    # ----
    # 1 (0-0-0) -> 12 (3-0-0)
    # 2 (0-1-0) -> 13 (3-1-0)
    # 3 (0-2-1) -> 14 (3-2-1)
    # 4 (1-3-2) -> 11 (1-9-4)
    # 5 (0-4-0) -> 13 (3-1-0)
    # 6 (0-5-1) -> 15.10 (3-5-3.2-8-1)
    # 7 (0-5-3) -> 15 (3-5-3)
    # 8 (2-6-1) -> 10 (2-8-1)
    def v7():
        class Salary(BaseModel):
            total_amount: int
            currency: str

        class Human(BaseModel):
            name: str
            surname: str
            age: int
            salary: Salary

        class Root(BaseModel):
            """Change person to Human"""
            human: Human

        return [Root, Human, Salary]

    index_builder.add('v7', v7(), {"0-0-0": Path('3-0-0'), "0-1-0": Path('3-1-0'), "0-2-1": Path('3-2-1'), "1-3-2": Path('1-9-4'),
                                   "0-4-0": Path('3-1-0'), "0-5-1": Path('3-5-3.2-8-1'), "0-5-3": Path('3-5-3'), "2-6-1": Path('2-8-1')})
    # pprint(index_builder.find_missing(v7()))
    pprint(index_builder.index)
    pprint(index_builder.property_pool.models)
    pprint(index_builder.property_pool.props)
    pprint(index_builder.property_pool.types)


    # Add mapping simulation (demonstrate how you mapped)

if __name__ == "__main__":
    main()
