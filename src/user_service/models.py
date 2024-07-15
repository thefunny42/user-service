import pydantic


class Identified(pydantic.BaseModel):
    id: str


class User(pydantic.BaseModel):
    name: str = pydantic.Field(max_length=256)
    email: pydantic.EmailStr = pydantic.Field(max_length=256)


class IdentifiedUser(Identified, User):
    pass


class Users(pydantic.BaseModel):
    users: list[IdentifiedUser] = pydantic.Field(default_factory=list)
