from repositories.tags_repository import TagsRepository


class TagsService:
    """
    Lógica de negocio relacionada a tags.
    """

    @staticmethod
    async def get_all_tags():
        return TagsRepository.get_all_tags()