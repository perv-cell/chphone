
from utils.logger.shemas_logger import RequestJsonLogSchema
from fastapi import Request, Response
from utils.logger.constants import EMPTY_VALUE, PORT
from starlette.types import Message
from starlette.middleware.base import RequestResponseEndpoint
import time
import http
import math
import json
import logging



logger = logging.getLogger("handlers/middlewares")

class LoggingMiddleware:
    """
    Middleware для обработки запросов и ответов с целью журналирования
    """
    @staticmethod
    async def get_protocol(request: Request) -> str:
        protocol = str(request.scope.get('type', ''))
        http_version = str(request.scope.get('http_version', ''))
        if protocol.lower() == 'http' and http_version:
            return f'{protocol.upper()}/{http_version}'
        return EMPTY_VALUE

    @staticmethod
    async def set_body(request: Request, body: bytes) -> None:
        async def receive() -> Message:
            return {'type': 'http.request', 'body': body}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        await self.set_body(request, body)
        return body

    async def __call__(
            self, request: Request, call_next: RequestResponseEndpoint,
            *args, **kwargs
    ):
        start_time = time.time()
        exception_object = None
        # Request Side
        try:
            raw_request_body = await request.body()
            # Последующие действия нужны,
            # чтобы не перезатереть тело запроса
						# и не уйти в зависание event-loop'a
            # при последующем получении тела ответа
            await self.set_body(request, raw_request_body)
            raw_request_body = await self.get_body(request)
            request_body = raw_request_body.decode()
        except Exception:
            request_body = EMPTY_VALUE

        server: tuple = request.get('server', ('localhost', PORT))
        request_headers: dict = dict(request.headers.items())
        # Response Side
        try:
            response = await call_next(request)
        except Exception as ex:
            response_body = bytes(
                http.HTTPStatus.INTERNAL_SERVER_ERROR.phrase.encode()
            )
            response = Response(
                content=response_body,
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.real,
            )
            exception_object = ex
            response_headers = {}
        else:
            response_headers = dict(response.headers.items())
            response_body = b''
            if hasattr(response, "body_iterator"):
                async for chunk in getattr(response, "body_iterator"):
                    response_body += chunk

            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        duration: int = math.ceil((time.time() - start_time) * 1000)

        request_json_fields = RequestJsonLogSchema(
            request_uri=str(request.url),
            request_referer=request_headers.get('referer', EMPTY_VALUE),
            request_protocol=await self.get_protocol(request),
            request_method=request.method,
            request_path=request.url.path,
            request_host=f'{server[0]}:{server[1]}',
            request_size=int(request_headers.get('content-length', 0)),
            request_content_type=request_headers.get(
                'content-type', EMPTY_VALUE),
            request_headers=json.dumps(request_headers),
            request_body=request_body,
            request_direction='in',
            remote_ip=getattr(request.client, 'host', 'unknown'),
            remote_port=getattr(request.client, 'port', 'unknown'),
            response_status_code=response.status_code,
            response_size=int(response_headers.get('content-length', 0)),
            response_headers=json.dumps(response_headers),
            response_body=response_body.decode(),
            duration=duration
        ).model_dump()
        # Хочется на каждый запрос читать
        # и понимать в сообщении самое главное,
        # поэтому message мы сразу делаем типовым
        message = f'{"Ошибка" if exception_object else "Ответ"} ' \
                  f'с кодом {response.status_code} ' \
                  f'на запрос {request.method} \"{str(request.url)}\", ' \
                  f'за {duration} мс'
        logger.info(
            message,
            extra={
                'request_json_fields': request_json_fields,
                'to_mask': True,
            },
            exc_info=exception_object,
        )
        return response
