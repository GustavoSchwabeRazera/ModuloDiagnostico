from __future__ import annotations

import logging

from diagnostico.inteligencia.provedor_api_comum import ErroProvedorInteligencia

logger = logging.getLogger(__name__)


class ProvedorComFallback:
    def __init__(self, primario, fallback=None):
        self.primario = primario
        self.fallback = fallback
        principal = getattr(primario, "nome", primario.__class__.__name__)
        reserva = getattr(fallback, "nome", fallback.__class__.__name__) if fallback else None
        self.nome = f"{principal}->{reserva}" if reserva else principal

    def analisar(self, entrada):
        try:
            return self.primario.analisar(entrada)
        except Exception as primary_error:
            if self.fallback is None:
                raise
            logger.warning(
                "Provedor primário indisponível; usando fallback. tipo=%s",
                type(primary_error).__name__,
            )
            try:
                return self.fallback.analisar(entrada)
            except Exception as fallback_error:
                raise ErroProvedorInteligencia(
                    "Provedores primário e secundário indisponíveis."
                ) from fallback_error
