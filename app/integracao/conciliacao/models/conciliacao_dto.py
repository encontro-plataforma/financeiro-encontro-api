from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConciliacaoDTO:
    descricao: str
    valor: float
    data: datetime
    tipo: str  # "entrada" | "saida"
    
    # opcionais / enriquecimento
    banco: Optional[str] = None
    identificador_externo: Optional[str] = None
    observacao: Optional[str] = None