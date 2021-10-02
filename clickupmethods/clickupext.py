from pyclickup import ClickUp
import tenacity
from typing import Union
from requests.models import Response
class ClickUpExt(ClickUp):

    WAIT_FIXED=1
    MAX_RETRIES=10**9
    class ErrException(Exception):
        pass
    @tenacity.retry(wait=tenacity.wait_fixed(WAIT_FIXED),
                    stop=tenacity.stop_after_attempt(MAX_RETRIES))
    def delete(
        self, path: str, raw: bool = False, **kwargs
    ) -> Union[list, dict, Response]:
        """makes a put request to the API"""
        request = self._req(path, method="delete", **kwargs)
        if 'err' in request:
            if self.delete.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request

    @tenacity.retry(wait=tenacity.wait_fixed(WAIT_FIXED),
                    stop=tenacity.stop_after_attempt(MAX_RETRIES))
    def get(self: ClickUp, path: str, raw: bool = False, **kwargs
            ) -> Union[list, dict, Response]:
        request = super().get(path, **kwargs)
        if 'err' in request:
            if self.get.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request

    @tenacity.retry(wait=tenacity.wait_fixed(WAIT_FIXED),
                    stop=tenacity.stop_after_attempt(MAX_RETRIES))
    def post(self: ClickUp, path: str, raw: bool = False, **kwargs
             ) -> Union[list, dict, Response]:
        request = super().post(path, **kwargs)
        if 'err' in request:
            if self.post.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request

    @tenacity.retry(wait=tenacity.wait_fixed(WAIT_FIXED),
                    stop=tenacity.stop_after_attempt(MAX_RETRIES))
    def put(self: ClickUp, path: str, raw: bool = False, **kwargs
            ) -> Union[list, dict, Response]:
        request = super().put(path, **kwargs)
        if 'err' in request:
            if self.put.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request