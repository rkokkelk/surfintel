import inspect
import json
import uuid
from hashlib import md5

from celery_singleton import Singleton


class TaskEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, uuid.UUID):
            return o.hex
        else:
            return super().default(o)


class UuidSafeSingleton(Singleton):
    abstract = True

    def generate_lock(self, task_name, task_args=None, task_kwargs=None):
        unique_on = self.unique_on
        task_args = task_args or []
        task_kwargs = task_kwargs or {}

        if unique_on:
            if isinstance(unique_on, str):
                unique_on = [unique_on]
            bound = inspect.signature(self.run).bind(*task_args, **task_kwargs).arguments
            unique_args = []
            unique_kwargs = {key: bound[key] for key in unique_on}
        else:
            unique_args = task_args
            unique_kwargs = task_kwargs

        str_args = json.dumps(unique_args, sort_keys=True, cls=TaskEncoder)
        str_kwargs = json.dumps(unique_kwargs, sort_keys=True, cls=TaskEncoder)
        task_hash = md5((task_name + str_args + str_kwargs).encode()).hexdigest()
        return self.singleton_config.key_prefix + task_hash
