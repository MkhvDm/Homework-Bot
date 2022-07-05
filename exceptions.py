class NotifiableError(Exception):
    pass


class ApiResponseNotCorrect(NotifiableError):
    pass


class PracticumApiErr(NotifiableError):
    pass


class UndefinedHWStatus(NotifiableError):
    pass


class TelegramSendErr(Exception):
    pass
