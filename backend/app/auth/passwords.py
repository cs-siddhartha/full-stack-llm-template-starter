import asyncio
import hashlib
import secrets


class PasswordHasher:
    """Hash passwords with scrypt and verify them without blocking the event loop."""

    _algorithm = "scrypt"
    _n = 2**14
    _r = 8
    _p = 1

    async def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = await asyncio.to_thread(self._derive, password, salt)
        return "$".join(
            (
                self._algorithm,
                str(self._n),
                str(self._r),
                str(self._p),
                salt.hex(),
                digest.hex(),
            )
        )

    async def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, n, r, p, salt, expected = encoded.split("$")
            if algorithm != self._algorithm:
                return False
            digest = await asyncio.to_thread(
                self._derive,
                password,
                bytes.fromhex(salt),
                int(n),
                int(r),
                int(p),
            )
            return secrets.compare_digest(digest, bytes.fromhex(expected))
        except (TypeError, ValueError):
            return False

    @classmethod
    def _derive(
        cls,
        password: str,
        salt: bytes,
        n: int | None = None,
        r: int | None = None,
        p: int | None = None,
    ) -> bytes:
        return hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n or cls._n,
            r=r or cls._r,
            p=p or cls._p,
            dklen=32,
        )
