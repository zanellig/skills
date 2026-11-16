# Optional tools for FastAPI applications

Select these additions according to the application's needs and the requested
work. They are optional, not dependencies to install in every FastAPI project.
Keep the core Python toolchain described in the parent skill.

## Development server

Use the [FastAPI CLI](https://fastapi.tiangolo.com/fastapi-cli/) when the project
needs a development command with automatic reload. It is available through
`fastapi[standard]`. Reuse the configured application entry point and run
`uv run fastapi dev`; reserve reload mode for development.

## Endpoint and async tests

Use [HTTPX with FastAPI's TestClient](https://fastapi.tiangolo.com/tutorial/testing/)
for endpoint tests that can run as synchronous pytest functions. Add HTTPX to
the development dependencies and use `TestClient` as a context manager when
tests require application startup and shutdown.

When tests must await database calls or other async operations, use
[HTTPX AsyncClient with ASGITransport and AnyIO](https://fastapi.tiangolo.com/advanced/async-tests/).
Declare the test dependencies, mark async tests with `pytest.mark.anyio`, and
select the backend supported by the application's dependencies. Ensure lifespan
startup and shutdown run when required; HTTPX's ASGI transport alone does not
trigger them. Restore dependency overrides after each test.

## Real service dependencies

Use [Testcontainers](https://testcontainers-python.readthedocs.io/en/latest/)
when integration tests need real PostgreSQL, Redis, or other services. Declare
it in the development dependencies, use pytest fixtures to manage container
lifetime, and pass connection settings into the application. Confirm Docker is
available locally and in the relevant CI job before relying on these tests.

## Tests generated from the API schema

Use [Schemathesis](https://schemathesis.readthedocs.io/en/stable/) when generated
tests from the application's OpenAPI schema would add coverage for validation,
response contracts, and unexpected inputs. Run against a disposable test
application and data, configure authentication where needed, and preserve
handwritten tests for business behavior. Add it as a development dependency
only when this testing approach is part of the task.
