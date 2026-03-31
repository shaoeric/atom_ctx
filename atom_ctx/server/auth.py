# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Authentication and authorization middleware for AtomCtx multi-tenant HTTP Server."""

import hmac
from typing import Optional

from fastapi import Depends, Header, Request

from atom_ctx.server.identity import RequestContext, ResolvedIdentity, Role
from atom_ctx_cli.exceptions import (
    InvalidArgumentError,
    PermissionDeniedError,
    UnauthenticatedError,
)
from atom_ctx_cli.session.user_id import UserIdentifier

_ROOT_IMPLICIT_TENANT_ALLOWED_PATHS = {
    "/api/v1/system/status",
    "/api/v1/system/wait",
    "/api/v1/debug/health",
}
_ROOT_IMPLICIT_TENANT_ALLOWED_PREFIXES = (
    "/api/v1/admin",
    "/api/v1/observer",
)


def _auth_mode(request: Request) -> str:
    config = getattr(request.app.state, "config", None)
    return getattr(config, "auth_mode", "api_key")


def _root_request_requires_explicit_tenant(path: str) -> bool:
    """Return True when a ROOT request targets tenant-scoped data APIs.

    Root still needs access to admin and monitoring endpoints without a tenant
    context. For data APIs, implicit fallback to default/default is misleading,
    so callers must provide explicit account and user headers.
    """
    if path in _ROOT_IMPLICIT_TENANT_ALLOWED_PATHS:
        return False
    if path.startswith(_ROOT_IMPLICIT_TENANT_ALLOWED_PREFIXES):
        return False
    return True


def _configured_root_api_key(request: Request) -> Optional[str]:
    config = getattr(request.app.state, "config", None)
    return getattr(config, "root_api_key", None)


def _extract_api_key(x_api_key: Optional[str], authorization: Optional[str]) -> Optional[str]:
    if not isinstance(x_api_key, str):
        x_api_key = None
    if not isinstance(authorization, str):
        authorization = None
    if x_api_key:
        return x_api_key
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


async def resolve_identity(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    x_atom_ctx_account: Optional[str] = Header(None, alias="X-AtomCtx-Account"),
    x_atom_ctx_user: Optional[str] = Header(None, alias="X-AtomCtx-User"),
    x_atom_ctx_agent: Optional[str] = Header(None, alias="X-AtomCtx-Agent"),
) -> ResolvedIdentity:
    """Resolve API key to identity.

    Strategy:
    - trusted mode: trust explicit account/user headers and return USER identity
    - api_key mode without manager: dev mode, return implicit ROOT/default identity
    - api_key mode with manager: resolve via APIKeyManager (root key first, then user key index)
    """
    auth_mode = _auth_mode(request)
    api_key_manager = getattr(request.app.state, "api_key_manager", None)
    api_key = _extract_api_key(x_api_key, authorization)

    if auth_mode == "trusted":
        configured_root_api_key = _configured_root_api_key(request)
        if configured_root_api_key:
            if not api_key:
                raise UnauthenticatedError("Missing API Key")
            if not hmac.compare_digest(api_key, configured_root_api_key):
                raise UnauthenticatedError("Invalid API Key")
        if not x_atom_ctx_account or not x_atom_ctx_user:
            raise InvalidArgumentError(
                "Trusted mode requests must include X-AtomCtx-Account and X-AtomCtx-User."
            )
        return ResolvedIdentity(
            role=Role.USER,
            account_id=x_atom_ctx_account,
            user_id=x_atom_ctx_user,
            agent_id=x_atom_ctx_agent or "default",
        )

    if api_key_manager is None:
        return ResolvedIdentity(
            role=Role.ROOT,
            account_id=x_atom_ctx_account or "default",
            user_id=x_atom_ctx_user or "default",
            agent_id=x_atom_ctx_agent or "default",
        )

    if not api_key:
        raise UnauthenticatedError("Missing API Key")

    identity = api_key_manager.resolve(api_key)
    identity.agent_id = x_atom_ctx_agent or "default"
    if identity.role == Role.ROOT:
        identity.account_id = x_atom_ctx_account or identity.account_id or "default"
        identity.user_id = x_atom_ctx_user or identity.user_id or "default"
    return identity


async def get_request_context(
    request: Request,
    identity: ResolvedIdentity = Depends(resolve_identity),
) -> RequestContext:
    """Convert ResolvedIdentity to RequestContext."""
    path = request.url.path
    auth_mode = _auth_mode(request)
    api_key_manager = getattr(request.app.state, "api_key_manager", None)
    if (
        auth_mode == "api_key"
        and api_key_manager is not None
        and identity.role == Role.ROOT
        and _root_request_requires_explicit_tenant(path)
    ):
        account_header = request.headers.get("X-AtomCtx-Account")
        user_header = request.headers.get("X-AtomCtx-User")
        if not account_header or not user_header:
            raise InvalidArgumentError(
                "ROOT requests to tenant-scoped APIs must include X-AtomCtx-Account "
                "and X-AtomCtx-User headers. Use a user key for regular data access."
            )

    if auth_mode == "trusted" and not identity.account_id:
        raise InvalidArgumentError("Trusted mode requests must include X-AtomCtx-Account.")
    if auth_mode == "trusted" and not identity.user_id:
        raise InvalidArgumentError("Trusted mode requests must include X-AtomCtx-User.")

    return RequestContext(
        user=UserIdentifier(
            identity.account_id or "default",
            identity.user_id or "default",
            identity.agent_id or "default",
        ),
        role=identity.role,
    )


def require_role(*allowed_roles: Role):
    """Dependency factory that checks role permission.

    Usage:
        @router.post("/admin/accounts")
        async def create_account(ctx: RequestContext = Depends(require_role(Role.ROOT))):
            ...
    """

    async def _check(ctx: RequestContext = Depends(get_request_context)):
        if ctx.role not in allowed_roles:
            raise PermissionDeniedError(
                f"Requires role: {', '.join(r.value for r in allowed_roles)}"
            )
        return ctx

    return Depends(_check)
