"""Cenários A e B — inserção crescente × inserção aleatória (AED II).

Responsável: I1 · Revisor: I2

Cenário A: chaves 1..n inseridas em ordem crescente (pior caso para BST comum).
Cenário B: as mesmas chaves numa permutação aleatória com semente registrada
(gerador.semente_permutacao — a mesma usada como base em C e D).

Regras de justiça (PLANO.md, seção 9):
- As contas são geradas UMA vez por (cenário, n, repetição) e a MESMA lista
  é entregue às duas árvores.
- Árvores novas a cada execução; contadores zerados antes do lote.
- Só o laço de inserções fica dentro do cronômetro (perf_counter).
- Modo detalhado desligado; validação feita depois, fora do cronômetro.
- Ordem alternada: repetição par AVL → RN; ímpar RN → AVL.

Uso pelo executor (I3):
    linhas = executar_cenario_insercao("A", 1000, repeticao=0)
Cada linha é um dict com exatamente as colunas de resultados_brutos.csv.

Execução direta (conferência rápida, não é a coleta oficial):
    python experimentos_insercao.py
"""

from __future__ import annotations

import time
from typing import Callable

import gerador
from avl import ArvoreAVL
from gerador import semente_permutacao  # fonte única das sementes (I3)

CENARIOS = ("A", "B")

COLUNAS_CSV = (
    "estrutura", "cenario", "n", "repeticao", "percentual", "tempo_s",
    "altura_antes", "altura_depois", "tamanho_antes", "tamanho_depois",
    "rotacoes", "recoloracoes", "nos_visitados", "buscas",
    "media_visitados", "valido",
)

NAO_SE_APLICA = "nao_se_aplica"

Estruturas = list[tuple[str, Callable[[], object]]]


def estruturas_padrao() -> Estruturas:
    """(nome no CSV, fábrica) de cada árvore. Import tardio da RN para que a
    AVL possa ser testada mesmo antes de rubro_negra.py existir."""
    from rubro_negra import ArvoreRubroNegra
    return [("AVL", ArvoreAVL), ("RN", ArvoreRubroNegra)]


def chaves_do_cenario(cenario: str, n: int, repeticao: int) -> list[int]:
    if cenario == "A":
        return gerador.chaves_crescentes(n)
    if cenario == "B":
        return gerador.permutacao(n, semente_permutacao(n, repeticao))
    raise ValueError(f"cenário de inserção desconhecido: {cenario!r} (use 'A' ou 'B')")


def ordem_das_estruturas(estruturas: Estruturas, repeticao: int) -> Estruturas:
    """Repetição par: ordem original (AVL → RN); ímpar: invertida (RN → AVL).
    Reduz o viés de quem roda primeiro (cache, aquecimento do interpretador)."""
    return list(estruturas) if repeticao % 2 == 0 else list(reversed(estruturas))


def _medir_insercao(nome: str, fabrica, contas: list, cenario: str, n: int,
                    repeticao: int) -> dict:
    arvore = fabrica()
    arvore.definir_modo_detalhado(False)
    arvore.resetar_estatisticas()
    inserir = arvore.inserir  # evita a busca do atributo a cada iteração

    inicio = time.perf_counter()
    for conta in contas:
        inserir(conta)
    tempo = time.perf_counter() - inicio

    # --- fora do cronômetro ---
    ok, _ = arvore.validar()
    valido = ok and arvore.tamanho() == len(contas)
    est = arvore.estatisticas()
    recoloracoes = est["recoloracoes"]

    return {
        "estrutura": nome,
        "cenario": cenario,
        "n": n,
        "repeticao": repeticao,
        "percentual": "",
        "tempo_s": tempo,
        "altura_antes": "",
        "altura_depois": arvore.altura(),
        "tamanho_antes": "",
        "tamanho_depois": arvore.tamanho(),
        "rotacoes": est["rotacoes"],
        "recoloracoes": NAO_SE_APLICA if recoloracoes is None else recoloracoes,
        "nos_visitados": "",
        "buscas": "",
        "media_visitados": "",
        "valido": valido,
        # não vai para o CSV: guardado para a análise A × B (opção B)
        "_casos_avl": arvore.rotacoes_por_caso() if hasattr(arvore, "rotacoes_por_caso") else None,
    }


def executar_cenario_insercao(cenario: str, n: int, repeticao: int,
                              estruturas: Estruturas | None = None) -> list[dict]:
    """Executa um cenário de inserção nas duas árvores e devolve uma linha por estrutura.

    As linhas vêm na ordem fixa (AVL, RN), independentemente da ordem de execução.
    A chave `_casos_avl` NÃO pertence ao CSV — use `linha_csv()` antes de gravar.
    """
    if estruturas is None:
        estruturas = estruturas_padrao()
    chaves = chaves_do_cenario(cenario, n, repeticao)
    contas = gerador.gerar_contas(chaves, semente_permutacao(n, repeticao))

    resultados = {
        nome: _medir_insercao(nome, fabrica, contas, cenario, n, repeticao)
        for nome, fabrica in ordem_das_estruturas(estruturas, repeticao)
    }
    return [resultados[nome] for nome, _ in estruturas]


def linha_csv(linha: dict) -> dict:
    """Só as colunas oficiais de resultados_brutos.csv."""
    return {coluna: linha[coluna] for coluna in COLUNAS_CSV}


# ---------------------------------------------------------------------- #
# Conferência rápida
# ---------------------------------------------------------------------- #
def _resumo(tamanhos=(100, 1000, 10000), repeticoes: int = 1) -> None:
    print(f"{'cen':>3} {'n':>6} {'estr':>4} {'altura':>6} {'rotações':>9} "
          f"{'recolor.':>13} {'tempo (ms)':>10} {'válido':>6}  casos AVL")
    for cenario in CENARIOS:
        for n in tamanhos:
            for rep in range(repeticoes):
                for l in executar_cenario_insercao(cenario, n, rep):
                    casos = l["_casos_avl"] or ""
                    print(f"{cenario:>3} {n:>6} {l['estrutura']:>4} {l['altura_depois']:>6} "
                          f"{l['rotacoes']:>9} {str(l['recoloracoes']):>13} "
                          f"{l['tempo_s'] * 1000:>10.2f} {str(l['valido']):>6}  {casos}")


if __name__ == "__main__":
    _resumo()