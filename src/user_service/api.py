from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse

from . import database, models, security

router = APIRouter(
    prefix="/api", dependencies=[Depends(security.validate_token)]
)


@router.get(
    "/users", response_model=models.Users, response_class=ORJSONResponse
)
async def list_users(
    repository: Annotated[database.UserRepository, Depends()]
):
    "List users as a JSON array"
    # We trust the format of the repository so we do not recreate models.
    return {"users": await repository.list()}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def add_user(
    repository: Annotated[database.UserRepository, Depends()],
    user: models.User,
):
    "Create a new user"
    if not await repository.add(user):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not add user.",
        )
    return user
