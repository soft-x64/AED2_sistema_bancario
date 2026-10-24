"""Geração reprodutível de dados para os experimentos (AED II).

Responsável: I3 · Revisor: I2

Toda aleatoriedade usa random.Random(semente) local — nunca o random global.
As sementes oficiais ficam AQUI (fonte única para os cenários A/B/C/D).
"""

from decimal import Decimal
import random

from modelos import Conta, criar_conta

SEMENTE_BASE = 2026


def semente_permutacao(n: int, repeticao: int) -> int:
    """Semente da permutação de B (também a base de C e D) e das contas."""
    return SEMENTE_BASE + 1000 * repeticao + n


def semente_subconjunto(n: int, repeticao: int, percentual: int) -> int:
    """Semente do subconjunto de chaves removidas no cenário D."""
    return SEMENTE_BASE + 500_000 + 1000 * repeticao + n + percentual


def chaves_crescentes(n: int) -> list[int]:
    """Gera uma lista de chaves em ordem crescente de 1 a n."""
    return list(range(1, n + 1))


def permutacao(n: int, semente: int) -> list[int]:
    """Gera uma permutação embaralhada das chaves de 1 a n usando a semente dada."""
    rng = random.Random(semente)
    chaves = list(range(1, n + 1))
    rng.shuffle(chaves)
    return chaves


def gerar_contas(chaves: list[int], semente: int) -> list[Conta]:
    """Gera objetos Conta válidos para uma lista de chaves informada."""
    rng = random.Random(semente)
    titulares = [
        "Ana Silva",
        "Bruno Souza",
        "Carlos Lima",
        "Diana Costa",
        "Eduardo Rocha",
        "Fernanda Dias",
        "Gabriel Martins",
        "Helena Ribeiro",
        "Igor Mendes",
        "Juliana Castro",
    ]
    tipos = ["CORRENTE", "POUPANCA"]
    contas = []

    for chave in chaves:
        titular = f"{rng.choice(titulares)} {chave}"
        agencia = str(rng.randint(1, 9999)).zfill(4)
        tipo = rng.choice(tipos)
        saldo = Decimal(str(round(rng.uniform(10.0, 50000.0), 2)))

        conta = criar_conta(
            numero=chave, titular=titular, agencia=agencia, tipo=tipo, saldo=saldo
        )
        contas.append(conta)

    return contas


def buscas(n: int, semente: int) -> list[int]:
    """Gera 2*n chaves para o cenário de busca (1..n existentes + n+1..2n ausentes) embaralhadas."""
    rng = random.Random(semente)
    todas = list(range(1, 2 * n + 1))
    rng.shuffle(todas)
    return todas


def subconjunto_remocao(
    chaves: list[int], percentual: int, semente: int
) -> list[int]:
    """Seleciona um subconjunto de chaves para remoção baseado no percentual dado."""
    rng = random.Random(semente)
    qtd = int(len(chaves) * (percentual / 100.0))
    copia = list(chaves)
    rng.shuffle(copia)
    return copia[:qtd]