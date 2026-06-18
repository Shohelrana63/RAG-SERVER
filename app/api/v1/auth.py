from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthData, LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.post("/register")
async def register(body: RegisterRequest):
    email = body.email.lower()
    if await User.find_one(User.email == email):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"message": "Email already registered."}},
        )

    user = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
    )
    await user.insert()

    return {
        "success": True,
        "data": AuthData(
            accessToken=create_access_token(str(user.id)),
            user=_user_out(user),
        ).model_dump(),
    }


@router.post("/login")
async def login(body: LoginRequest):
    user = await User.find_one(User.email == body.email.lower())
    if not user or not verify_password(body.password, user.password_hash):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": {"message": "Invalid credentials."}},
        )

    return {
        "success": True,
        "data": AuthData(
            accessToken=create_access_token(str(user.id)),
            user=_user_out(user),
        ).model_dump(),
    }


@router.delete("/me")
async def delete_user(user: User = Depends(get_current_user)):
    await user.delete()
    return {"success": True, "data": None}


@router.get("/all-users")
async def all_users():
    users = await User.find_all().to_list()
    return {
        "success": True,
        "data": [UserOut(id=str(user.id), name=user.name, email=user.email, role=user.role).model_dump() for user in users],
    }