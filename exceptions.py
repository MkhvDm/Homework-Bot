class ApiResponseNotCorrect(Exception):
    pass


class PracticumApiErr(Exception):
    def __init__(self, err_key):
        super().__init__()
        self.err_key = err_key


class TelegramSendErr(Exception):
    pass


class UndefinedHWStatus(Exception):
    pass