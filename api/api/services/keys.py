import binascii
import logging
import math
import time
from typing import TypeVar

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDSA,
    SECP256R1,
    EllipticCurvePublicKey,
    EllipticCurvePublicNumbers,
)
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from pydantic import BaseModel

from core.domain.errors import InvalidToken
from core.utils.strings import b64_urldecode


class JWK(BaseModel):
    kty: str
    x: str
    y: str
    crv: str
    id: str

    def public_key(self) -> EllipticCurvePublicKey:
        x_bytes = b64_urldecode(self.x)
        y_bytes = b64_urldecode(self.y)

        x_int = int.from_bytes(x_bytes, "big")
        y_int = int.from_bytes(y_bytes, "big")

        if self.crv != "P-256" or self.kty != "EC":
            raise AssertionError("Only P-256 is supported")

        # TODO: support other curves
        public_numbers = EllipticCurvePublicNumbers(x_int, y_int, SECP256R1())
        return public_numbers.public_key(default_backend())


class JWTHeader(BaseModel):
    alg: str
    kid: str = "1"

    @classmethod
    def from_jwt_part(cls, part: str) -> "JWTHeader":
        decoded_header = b64_urldecode(part)
        return cls.model_validate_json(decoded_header)


class JWKS(BaseModel):
    keys: list[JWK]


class Claims(BaseModel):
    exp: int
    iat: int = 0


T = TypeVar("T", bound=Claims)


class KeyRing:
    def __init__(self, jwks_url: str, keys: dict[str, EllipticCurvePublicKey] = {}) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self.jwks_url = jwks_url
        if not jwks_url and not keys:
            raise ValueError("Either jwks_url or keys must be provided")
        self.key_cache = keys

    async def _refresh_keys(self) -> None:
        """Refresh the key cache"""
        if not self.jwks_url:
            return

        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            jwks = JWKS.model_validate(response.json())

        for key in jwks.keys:
            self.key_cache[key.id] = key.public_key()

    async def _get_key(self, header: JWTHeader) -> EllipticCurvePublicKey:
        if header.alg != "ES256":
            raise AssertionError("Only ES256 is supported")

        if header.kid not in self.key_cache:
            try:
                await self._refresh_keys()
            except (httpx.HTTPStatusError, httpx.ConnectError):
                # We should
                self._logger.exception(
                    "Failed to fetch keys",
                    extra={
                        "cached_keys": list(self.key_cache.keys()),
                        "jwks_url": self.jwks_url,
                    },
                )

        try:
            return self.key_cache[header.kid]
        except KeyError:
            # This would mean that the token is using a key that does not exist
            # or that refreshing the keys above failed.
            # This should really not happen so we choose to return a 500.
            raise ValueError(f"Kid {header.kid} not available, Available key ids: {list(self.key_cache.keys())}")

    async def verify(self, token: str, returns: type[T]) -> T:
        """Verify a token and return the associated claims"""
        splits = token.split(".")
        if len(splits) != 3:
            raise InvalidToken("Invalid jwt")

        try:
            header = JWTHeader.from_jwt_part(splits[0])
        except (binascii.Error, ValueError):
            raise InvalidToken("Invalid header encoding")
        key = await self._get_key(header)

        try:
            signature = b64_urldecode(splits[2])
        except binascii.Error:
            raise InvalidToken("Invalid signature encoding")
        signed = ".".join(splits[:2]).encode()

        verify_signature(signed, signature, key)

        claims = returns.model_validate_json(b64_urldecode(splits[1]))

        now = time.time()
        if claims.exp < now:
            raise InvalidToken("Token expired")

        if claims.iat > now:
            raise InvalidToken("Token issued in the future")

        return claims


def verify_signature(signed: bytes, signature: bytes, key: EllipticCurvePublicKey) -> None:
    component_length = int(math.ceil(key.key_size / 8.0))
    r_bytes = signature[:component_length]
    s_bytes = signature[component_length:]
    r = int.from_bytes(r_bytes, "big")
    s = int.from_bytes(s_bytes, "big")
    der_signature = encode_dss_signature(r, s)

    try:
        key.verify(der_signature, signed, ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise InvalidToken("Invalid signature")
