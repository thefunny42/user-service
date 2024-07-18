from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import ORJSONResponse
from whtft.metrics import Metrics
from whtft.security import Checker

from . import database, models, settings

security = Checker(settings.settings)

router = APIRouter(prefix="/api", dependencies=[Depends(security)])

metrics = Metrics(prefix="userservice")


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_class=ORJSONResponse,
)
@metrics.measure()
async def add_user(
    repository: Annotated[database.UserRepository, Depends()],
    user: models.User,
):
    "Create a new user"
    if (added_user := await repository.add(user)) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not add user.",
        )
    return added_user


@router.get(
    "/users", response_model=models.Users, response_class=ORJSONResponse
)
@metrics.measure()
async def list_users(
    repository: Annotated[database.UserRepository, Depends()]
):
    "List users as a JSON array"
    return {"users": await repository.list()}


@router.get(
    "/users/{user_id}",
    response_model=models.IdentifiedUser,
    response_class=ORJSONResponse,
)
@metrics.measure()
async def get_user(
    repository: Annotated[database.UserRepository, Depends()], user_id: str
):
    "Get a user"
    if (user := await repository.get(user_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user


@router.delete("/users/{user_id}")
@metrics.measure()
async def delete_user(
    repository: Annotated[database.UserRepository, Depends()], user_id: str
):
    "Delete a user"
    if await repository.delete(user_id) is False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
