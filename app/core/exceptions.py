from fastapi import HTTPException

class NotFoundException(HTTPException):
    def __init__(self, resource: str = "Recurso"):
        super().__init__(
            status_code=404,
            detail=f"{resource} não encontrado"
        )
        
class BadRequestException(HTTPException):
    def __init__(self, detail="Requisição inválida"):
        super().__init__(status_code=400, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail="Não autorizado"):
        super().__init__(status_code=401, detail=detail)