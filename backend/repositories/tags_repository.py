import json
from core.config import r


class TagsRepository:
    """
    Acceso directo a Redis para lectura de tags actuales.
    """

    @staticmethod
    def get_all_tags():
        keys = r.keys("tag_current:*")
        tags = {}

        for key in keys:
            tag_path = key.replace("tag_current:", "")
            raw_value = r.get(key)

            if raw_value:
                tags[tag_path] = json.loads(raw_value)

        return tags