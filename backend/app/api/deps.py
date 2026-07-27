from typing import Annotated

from litestar.params import HeaderParameter


def provide_owner_id(
    x_user_id: Annotated[str | None, HeaderParameter(name="X-User-Id", required=False)] = None,
) -> str:
    # Supabase JWT verification can be added once project credentials are supplied.
    # Until then, this keeps local development and APK smoke tests simple.
    return x_user_id or "local-demo-user"
