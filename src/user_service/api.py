from typing import Annotated

from fastapi import APIRouter, Depends, status

from . import models, security

users = models.Users()


def get_users():
    return users


Users = Annotated[models.Users, Depends(get_users)]

router = APIRouter(
    prefix="/api", dependencies=[Depends(security.validate_token)]
)


@router.get("/users")
def get_users_endpoint(users: Users):
    "List users as a JSON array"
    return users


@router.post("/users", status_code=status.HTTP_201_CREATED)
def post_users_endpoint(users: Users, user: models.User):
    "Create a new user"
    users.users.append(user)
    return user
