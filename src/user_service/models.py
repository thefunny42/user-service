import pydantic


class User(pydantic.BaseModel):
    name: str = pydantic.Field(max_length=256)
    email: pydantic.EmailStr = pydantic.Field(max_length=256)


class Users(pydantic.BaseModel):
    users: list[User] = pydantic.Field(default_factory=list)
