from backend.services.auth_service import signup_user, login_user


def signup_controller(data: dict):
    return signup_user(data)


def login_controller(data: dict):
    return login_user(data)