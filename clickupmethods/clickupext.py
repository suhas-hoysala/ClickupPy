from pyclickup import ClickUp
import tenacity
from typing import Union
from requests.models import Response
class ClickUpExt(ClickUp):

    class ErrException(Exception):
        pass
    @tenacity.retry(wait=tenacity.wait_fixed(15),
                    stop=tenacity.stop_after_attempt(8))
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

    @tenacity.retry(wait=tenacity.wait_fixed(15),
                    stop=tenacity.stop_after_attempt(8))
    def get(self: ClickUp, path: str, raw: bool = False, **kwargs
            ) -> Union[list, dict, Response]:
        request = super().get(path, **kwargs)
        if 'err' in request:
            if self.get.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request

    @tenacity.retry(wait=tenacity.wait_fixed(15),
                    stop=tenacity.stop_after_attempt(8))
    def post(self: ClickUp, path: str, raw: bool = False, **kwargs
             ) -> Union[list, dict, Response]:
        request = super().post(path, **kwargs)
        if 'err' in request:
            if self.post.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request

    @tenacity.retry(wait=tenacity.wait_fixed(15),
                    stop=tenacity.stop_after_attempt(8))
    def put(self: ClickUp, path: str, raw: bool = False, **kwargs
            ) -> Union[list, dict, Response]:
        request = super().put(path, **kwargs)
        if 'err' in request:
            if self.put.retry.statistics['attempt_number'] == 8:
                return request
            raise ClickUpExt.ErrException()
        return request