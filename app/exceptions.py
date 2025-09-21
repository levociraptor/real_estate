class NotAllowedContentType(Exception):
    pass


class FileTooBig(Exception):
    pass


class ImageNotFound(Exception):
    pass


class ImageSaveWithError(Exception):
    pass


class ImageNotProcessedYetError(Exception):
    pass


class DBHealtCheckException(Exception):
    pass


class RabbitHealthCheckException(Exception):
    pass
