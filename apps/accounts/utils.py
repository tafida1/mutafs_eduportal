import secrets
import string


def generate_temporary_password(length=10):
    chars = string.ascii_letters + string.digits + "@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))