import pytest

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    ApiGatewayResolver,
    LambdaFunctionUrlResolver,
    Response,
)
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.event_handler.router import (
    ALBRouter,
    APIGatewayHttpRouter,
    APIGatewayRouter,
    LambdaFunctionUrlRouter,
    Router,
)
from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    LambdaFunctionUrlEvent,
)
from tests.functional.utils import load_event


def test_alb_router_event_type():
    app = ALBResolver()
    router = ALBRouter()

    @router.route(rule="/lambda", method=["GET"])
    def foo():
        assert type(router.current_event) is ALBEvent
        return Response(status_code=200, body="routed")

    app.include_router(router)
    result = app(load_event("albEvent.json"), {})
    assert result["body"] == "routed"


def test_apigateway_router_event_type():
    app = APIGatewayRestResolver()
    router = APIGatewayRouter()

    @router.route(rule="/my/path", method=["GET"])
    def foo():
        assert type(router.current_event) is APIGatewayProxyEvent
        return Response(status_code=200, body="routed")

    app.include_router(router)
    result = app(load_event("apiGatewayProxyEvent.json"), {})
    assert result["body"] == "routed"


def test_apigatewayhttp_router_event_type():
    app = APIGatewayHttpResolver()
    router = APIGatewayHttpRouter()

    @router.route(rule="/my/path", method=["POST"])
    def foo():
        assert type(router.current_event) is APIGatewayProxyEventV2
        return Response(status_code=200, body="routed")

    app.include_router(router)
    result = app(load_event("apiGatewayProxyV2Event.json"), {})
    assert result["body"] == "routed"


def test_lambda_function_url_router_event_type():
    app = LambdaFunctionUrlResolver()
    router = LambdaFunctionUrlRouter()

    @router.route(rule="/", method=["GET"])
    def foo():
        assert type(router.current_event) is LambdaFunctionUrlEvent
        return Response(status_code=200, body="routed")

    app.include_router(router)
    result = app(load_event("lambdaFunctionUrlEvent.json"), {})
    assert result["body"] == "routed"


@pytest.mark.parametrize("router,resolver,event_file", [
    (ALBRouter, ALBResolver, "albEvent.json"),
    (APIGatewayRouter, APIGatewayRestResolver, "apiGatewayProxyEvent.json"),
    (APIGatewayHttpRouter, APIGatewayHttpResolver, "apiGatewayProxyV2Event.json"),
    (LambdaFunctionUrlRouter, LambdaFunctionUrlResolver, "lambdaFunctionUrlEvent.json"),
])
def test_path_parameters_in_context(
    router: Router,
    resolver: ApiGatewayResolver,
    event_file: str,
) -> None:
    app = resolver()
    router = router()
    param_key, param_value = "key", "value"

    def bar(app: APIGatewayRestResolver, next_middleware: NextMiddleware) -> Response:
        raise Exception(app.current_event)
        assert app.context.path_parameters == {param_key: param_value}
        return next_middleware(app)

    @router.route(rule="/<key>", method=["GET"], middlewares=[bar])
    def foo(key: str) -> Response:
        assert key == param_value
        return Response(status_code=200, body="routed")

    app.include_router(router)
    event = load_event(event_file)
    event["path"] = "/" + param_value
    result = app(event, {})
    assert result["body"] == "routed"
