from pydantic import BaseModel


# GLOBAL INDEX
# name:str (Person) - 1
# surname:str (Person) - 2
# age:int (Person) - 3
# person: Person (Root) - 4
# last_name:str (Person) - 5
# salary: int (Person) - 6
# salary: Salary (Person) - 7
# amount: int (Salary) - 8
# currency: str (Salary) - 9
# total_amount: int (Salary) - 10
# human: Human (Root) - 11
# name:str (Human) - 12
# surname:str (Human) - 13
# age:int (Human) - 14
# salary: Salary (Human) - 15

# Index (v1)
# 1
# 2
# 3
# 4

def v1():
    """Init"""

    class Person(BaseModel):
        name: str
        surname: str
        age: int

    class Root(BaseModel):
        person: Person

    return Root


# Index (v2)
# 1
# 3
# 4
# 5
# ----
# 2 -> 5

def v2():
    """Change surname to last_name"""

    class Person(BaseModel):
        name: str
        last_name: str
        age: int

    class Root(BaseModel):
        person: Person

    return Root


# Index (v3)
# 1
# 2
# 3
# 4
# ----
# 5 -> 2

def v3():
    class Person(BaseModel):
        """Change last_name to surname"""
        name: str
        surname: str
        age: int

    class Root(BaseModel):
        person: Person

    return Root


# Index (v4)
# 1
# 2
# 3
# 4
# 6
# ----
# 5 -> 2

def v4():
    class Person(BaseModel):
        """Add salary"""
        name: str
        surname: str
        age: int
        salary: int

    class Root(BaseModel):
        person: Person

    return Root


# Index (v5)
# 1
# 2
# 3
# 4
# 7
# 8
# 9
# ----
# 5 -> 2
# 6 -> 7.8

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

    return Root


# Index (v6)
# 1
# 2
# 3
# 4
# 7
# 9
# 10
# ----
# 5 -> 2
# 6 -> 7.10
# 8 -> 10

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

    return Root


# Index (v7)
# 9
# 10
# 11
# 12
# 13
# 14
# 15
# ----
# 1 -> 12
# 2 -> 13
# 3 -> 14
# 4 -> 11
# 5 -> 13
# 6 -> 15.10
# 7 -> 15
# 8 -> 10
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

    return Root


if __name__ == "__main__":
    main()
