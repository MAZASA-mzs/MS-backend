class NotFoundError(Exception):
    """Выбрасывается, когда сущность не найдена (будет 404)"""

    def __init__(self, entity_name: str):
        self.entity_name = entity_name
        self.message = f"{entity_name} not found"
        super().__init__(self.message)


class InvalidReferenceError(Exception):
    """Выбрасывается, когда связанный ID не существует (будет 422)"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Ошибки бизнес логики, например "Аккаунт уже привязан" (будет 400)"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
