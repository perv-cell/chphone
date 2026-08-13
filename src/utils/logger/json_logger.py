import datetime
import json
import logging
import traceback
from typing import Any, Dict

from utils.logger.shemas_logger import BaseJsonLogSchema
from config import get_settings

settings = get_settings()

class JSONLogFormatter(logging.Formatter):
    """
    Кастомизированный класс-форматер для логов в формате json с отступами
    """

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        """
        Преобразование объекта журнала в json с отступами
        """
        log_object: dict = self._format_log_object(record)
        return json.dumps(
            log_object,
            indent=2,
            ensure_ascii=False,
            sort_keys=False
        )

    def _format_log_object(self,record: logging.LogRecord) -> dict:
        """
        Перевод записи объекта журнала в json формат
        """
        now = datetime.datetime.fromtimestamp(record.created).astimezone().replace(microsecond=0).isoformat()
        message = record.getMessage()
        duration = record.duration if hasattr(record, 'duration') else record.msecs

        json_log_fields = BaseJsonLogSchema(
            thread=record.process,
            timestamp=now,
            level=record.levelno,
            level_name=record.levelname,
            message=message,
            source=record.name,
            duration=duration,
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            app_env=settings.ENVIRONMENT,
        )

        if hasattr(record, 'props'):
            json_log_fields.props = record.props

        if record.exc_info:
            json_log_fields.exceptions = traceback.format_exception(*record.exc_info)
        elif record.exc_text:
            json_log_fields.exceptions = record.exc_text

        json_log_object = json_log_fields.model_dump(
            exclude_unset=True,
            by_alias=True,
        )

        if hasattr(record, 'request_json_fields'):
            if 'response_body' in record.request_json_fields:
                record.request_json_fields['response_body'] = self._format_body(
                    record.request_json_fields.get('response_body')
                )
            json_log_object.update(record.request_json_fields)

        return json_log_object


    def _format_body(self,body: Any, max_length: int = 3000) -> str:
        """
        Форматирует тело ответа для логирования с отступами
        """
        if body is None:
            return ""

        if hasattr(body, 'model_dump'):
            body = body.model_dump()

        if isinstance(body, (dict, list)):
            try:
                # ✅ Форматируем с отступами
                formatted = json.dumps(
                    body,
                    indent=2,
                    ensure_ascii=False,
                    default=str
                )

                return formatted
            except Exception as e:
                return f"Ошибка форматирования: {e}"

        return str(body)

def write_log(msg):
    if isinstance(msg, (dict, list)):
        pretty_json = json.dumps(msg, indent=2, ensure_ascii=False)
        print(pretty_json, end="\n")
    else:
        print(msg,end="\n")
