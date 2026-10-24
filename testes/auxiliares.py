"""Utilitários de teste da AVL.

`ContaFake` substitui a Conta do I3 enquanto modelos.py não existe; tem os
mesmos atributos, então os testes continuam valendo depois da integração.

`verificar_avl` confere as propriedades por conta própria, sem usar nada da
árvore além da raiz — é a "contagem independente" pedida no plano.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ContaFake:
    numero: int
    titular: str = "Titular Teste"
    agencia: str = "0001"
    tipo: str = "CORRENTE"
    saldo: Decimal = Decimal("0.00")


def conta(numero: int, **atributos) -> ContaFake:
    return ContaFake(numero, **atributos)


def chaves(contas) -> list[int]:
    return [c.numero for c in contas]


def verificar_avl(arvore) -> tuple[int, int]:
    """Lança AssertionError se a AVL estiver inválida. Retorna (altura, tamanho) reais."""

    def visitar(no, minimo, maximo):
        if no is None:
            return -1, 0
        k = no.conta.numero
        assert (minimo is None or k > minimo) and (maximo is None or k < maximo), (
            f"ordem violada em {k} (limites {minimo}, {maximo})"
        )
        he, te = visitar(no.esquerda, minimo, k)
        hd, td = visitar(no.direita, k, maximo)
        assert abs(he - hd) <= 1, f"FB={he - hd} em {k}"
        h = 1 + max(he, hd)
        assert no.altura == h, f"altura armazenada {no.altura} ≠ real {h} em {k}"
        return h, te + td + 1

    altura, tamanho = visitar(arvore._raiz, None, None)
    assert arvore.altura() == altura, "altura() diverge da contagem real"
    assert arvore.tamanho() == tamanho, "tamanho() diverge da contagem real"
    return altura, tamanho