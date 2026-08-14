from backend.services.auth_service import signup_user, login_user


async def signup_controller(data: dict):
    return await signup_user(data)


async def login_controller(data: dict):
    return await login_user(data)