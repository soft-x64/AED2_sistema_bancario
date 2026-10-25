"""Utilitários de teste da AVL.

`conta()` cria uma Conta REAL (modelos.py do I3) com atributos padrão válidos,
para os testes exercitarem a árvore exatamente como a aplicação a usa.

`verificar_avl` confere as propriedades por conta própria, sem usar nada da
árvore além da raiz — é a "contagem independente" pedida no plano.
"""

from __future__ import annotations

from decimal import Decimal

from modelos import Conta

_PADRAO = {
    "titular": "Titular Teste",
    "agencia": "0001",
    "tipo": "CORRENTE",
    "saldo": Decimal("0.00"),
}


def conta(numero: int, **atributos) -> Conta:
    """Conta válida com o número dado; qualquer atributo pode ser sobrescrito."""
    return Conta(numero, **{**_PADRAO, **atributos})


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
