
import base64
import hashlib
import hmac
import secrets


class Security:

    """
    Handles password hashing and verification.
    Uses PBKDF2-HMAC-SHA256 with random salts.
    """

    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 600_000
    SALT_LENGTH = 16

    @classmethod
    def hash_password(cls, password: str) -> str:

        if not isinstance(password, str) or not password:
            raise ValueError("Password cannot be empty.")

        salt = secrets.token_bytes(cls.SALT_LENGTH)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.ITERATIONS
        )

        encoded_salt = base64.urlsafe_b64encode(
            salt
        ).decode("ascii")

        encoded_hash = base64.urlsafe_b64encode(
            password_hash
        ).decode("ascii")

        return (
            f"{cls.ALGORITHM}$"
            f"{cls.ITERATIONS}$"
            f"{encoded_salt}$"
            f"{encoded_hash}"
        )

    @classmethod
    def verify_password(
        cls,
        password: str,
        stored_hash: str
    ) -> bool:

        if not isinstance(password, str):
            return False

        if not isinstance(stored_hash, str):
            return False

        try:

            algorithm, iterations, salt, expected_hash = (
                stored_hash.split("$")
            )

            if algorithm != cls.ALGORITHM:
                return False

            iterations = int(iterations)

            if not 100_000 <= iterations <= 2_000_000:
                return False

            salt_bytes = base64.b64decode(
                salt,
                altchars=b"-_",
                validate=True
            )

            expected_bytes = base64.b64decode(
                expected_hash,
                altchars=b"-_",
                validate=True
            )

            actual_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt_bytes,
                iterations
            )

            return hmac.compare_digest(
                actual_hash,
                expected_bytes
            )

        except (ValueError, TypeError):
            return False
