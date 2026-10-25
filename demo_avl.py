"""Demonstração passo a passo da AVL (I1) — útil para estudo e para a defesa.

Uso:
    python demo_avl.py            # roda tudo de uma vez
    python demo_avl.py --pausar   # espera ENTER entre as etapas
"""

import sys
from decimal import Decimal

from avl import ArvoreAVL
from modelos import Conta

PAUSAR = "--pausar" in sys.argv


def conta(numero: int) -> Conta:
    return Conta(numero, f"Titular {numero}", "0001", "CORRENTE", Decimal("100.00"))


def titulo(texto: str) -> None:
    if PAUSAR:
        input("\n[ENTER para continuar]")
    print("\n" + "=" * 64)
    print(texto)
    print("=" * 64)


def mostrar(arvore: ArvoreAVL) -> None:
    print("\nÁrvore:")
    print(arvore.exibir())
    e = arvore.estatisticas()
    print(f"\naltura={arvore.altura()}  tamanho={arvore.tamanho()}  "
          f"rotações={e['rotacoes']}  casos={arvore.rotacoes_por_caso()}")
    ok, erros = arvore.validar()
    print(f"validar() → {'válida' if ok else erros}")


def inserir_detalhado(sequencia, descricao: str) -> ArvoreAVL:
    titulo(f"{descricao}: inserir {', '.join(map(str, sequencia))}")
    arvore = ArvoreAVL()
    arvore.definir_modo_detalhado(True)
    for k in sequencia:
        arvore.inserir(conta(k))
    mostrar(arvore)
    return arvore


# 1. Os quatro casos de rotação
inserir_detalhado([30, 20, 10], "Caso LL (pende à esquerda, filho à esquerda) → 1 rotação")
inserir_detalhado([10, 20, 30], "Caso RR (pende à direita, filho à direita) → 1 rotação")
inserir_detalhado([30, 10, 20], "Caso LR (esquerda, depois direita) → rotação dupla = 2")
inserir_detalhado([10, 30, 20], "Caso RL (direita, depois esquerda) → rotação dupla = 2")

# 2. Busca contando nós visitados
titulo("Busca: cada nó comparado conta 1 visita")
arvore = ArvoreAVL()
for k in [50, 30, 70, 20, 40, 60, 80]:
    arvore.inserir(conta(k))
arvore.definir_modo_detalhado(True)
arvore.buscar(40)
arvore.buscar(65)
e = arvore.estatisticas()
print(f"\nbuscas={e['buscas']}  nós visitados={e['nos_visitados']}  "
      f"média={e['nos_visitados'] / e['buscas']:.1f}")

# 3. Remoção com 2 filhos
titulo("Remoção com 2 filhos: o sucessor assume o lugar")
arvore = ArvoreAVL()
for k in [20, 10, 30, 25, 40]:
    arvore.inserir(conta(k))
print("Antes:")
print(arvore.exibir())
arvore.definir_modo_detalhado(True)
removida = arvore.remover(20)
print(f"\nremover(20) devolveu: {removida}")
mostrar(arvore)

# 4. Remoção que corrige vários níveis (árvore de Fibonacci)
titulo("Remoção em vários níveis: árvore de Fibonacci de altura 4, remover 12")
arvore = ArvoreAVL()
for k in [8, 5, 11, 3, 7, 10, 12, 2, 4, 6, 9, 1]:
    arvore.inserir(conta(k))
print("Antes:")
print(arvore.exibir())
arvore.resetar_estatisticas()
arvore.definir_modo_detalhado(True)
print()
arvore.remover(12)
mostrar(arvore)

# 5. Ordem crescente × aleatória
titulo("Ordem de inserção: crescente × aleatória (1.000 contas)")
import random
for nome, chaves in [("crescente", list(range(1, 1001))),
                     ("aleatória", random.Random(2026).sample(range(1, 1001), 1000))]:
    arvore = ArvoreAVL()
    for k in chaves:
        arvore.inserir(conta(k))
    print(f"{nome:>10}: altura={arvore.altura():>2}  "
          f"rotações={arvore.estatisticas()['rotacoes']:>4}  casos={arvore.rotacoes_por_caso()}")

print("\nFim da demonstração.")
