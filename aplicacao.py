"""Coordenação das duas árvores do Sistema Bancário (AED II).

Responsável: I3 · Revisor: I2

A aplicação mantém uma AVL e uma Rubro-Negra independentes com a MESMA
coleção de contas:
- cadastro e remoção são enviados às duas árvores e os retornos comparados;
- consultas (busca, mínimo/máximo, caminhamentos, altura, tamanho, exibição,
  estatísticas) usam a árvore ativa escolhida no menu.
"""

from __future__ import annotations

from avl import ArvoreAVL
from modelos import Conta, criar_conta, normalizar_numero
from rubro_negra import ArvoreRubroNegra

NOMES_ARVORE = {"AVL": "AVL", "RN": "RN", "RUBRO-NEGRA": "RN", "RUBRO NEGRA": "RN"}


class InconsistenciaEntreArvores(Exception):
    """As duas árvores devolveram resultados diferentes para a mesma operação."""


class ContaDuplicada(ValueError):
    """Já existe uma conta com esse número (a coleção não foi alterada)."""


class AplicacaoBancaria:
    """Fachada usada pelo menu: uma coleção de contas guardada em duas árvores."""

    def __init__(self) -> None:
        self.avl = ArvoreAVL()
        self.rn = ArvoreRubroNegra()
        self.arvore_ativa_nome = "AVL"

    # ------------------------------------------------------------------ #
    # Árvore ativa
    # ------------------------------------------------------------------ #
    @property
    def arvore_ativa(self):
        return self.avl if self.arvore_ativa_nome == "AVL" else self.rn

    def definir_arvore_ativa(self, nome: str) -> None:
        chave = " ".join(str(nome).upper().split())
        if chave not in NOMES_ARVORE:
            raise ValueError("Árvore inválida. Escolha AVL ou RN.")
        self.arvore_ativa_nome = NOMES_ARVORE[chave]

    # ------------------------------------------------------------------ #
    # Operações que alteram a coleção (vão para as duas árvores)
    # ------------------------------------------------------------------ #
    def cadastrar(self, numero, titular, agencia, tipo, saldo) -> Conta:
        """Valida, cria a conta e a insere nas duas árvores.

        Raises:
            ValueError: algum campo é inválido (mensagem vinda de modelos.py).
            ContaDuplicada: o número já existe (nada é alterado).
            InconsistenciaEntreArvores: as árvores divergiram.
        """
        conta = criar_conta(numero, titular, agencia, tipo, saldo)
        inseriu_avl = self.avl.inserir(conta)
        inseriu_rn = self.rn.inserir(conta)

        if inseriu_avl != inseriu_rn:
            raise InconsistenciaEntreArvores(
                f"Divergência na inserção da conta {conta.numero}: "
                f"AVL={inseriu_avl}, RN={inseriu_rn}"
            )
        if not inseriu_avl:
            raise ContaDuplicada(f"Já existe uma conta com o número {conta.numero}.")
        return conta

    def remover(self, numero) -> Conta | None:
        """Remove das duas árvores. Devolve a conta removida ou None se não existir."""
        numero = normalizar_numero(numero)
        removida_avl = self.avl.remover(numero)
        removida_rn = self.rn.remover(numero)

        if removida_avl != removida_rn:  # Conta é dataclass: compara todos os campos
            raise InconsistenciaEntreArvores(
                f"Divergência na remoção da conta {numero}: "
                f"AVL={removida_avl}, RN={removida_rn}"
            )
        return removida_avl

    # ------------------------------------------------------------------ #
    # Consultas (usam a árvore ativa)
    # ------------------------------------------------------------------ #
    def buscar(self, numero) -> Conta | None:
        return self.arvore_ativa.buscar(normalizar_numero(numero))

    def minimo(self) -> Conta | None:
        return self.arvore_ativa.minimo()

    def maximo(self) -> Conta | None:
        return self.arvore_ativa.maximo()

    def pre_ordem(self) -> list[Conta]:
        return self.arvore_ativa.pre_ordem()

    def em_ordem(self) -> list[Conta]:
        return self.arvore_ativa.em_ordem()

    def pos_ordem(self) -> list[Conta]:
        return self.arvore_ativa.pos_ordem()

    def altura(self) -> int:
        return self.arvore_ativa.altura()

    def tamanho(self) -> int:
        return self.arvore_ativa.tamanho()

    def exibir(self) -> str:
        return self.arvore_ativa.exibir()

    def estatisticas(self) -> dict:
        return self.arvore_ativa.estatisticas()

    # ------------------------------------------------------------------ #
    # Operações aplicadas às duas árvores
    # ------------------------------------------------------------------ #
    def resetar_estatisticas(self) -> None:
        self.avl.resetar_estatisticas()
        self.rn.resetar_estatisticas()

    def definir_modo_detalhado(self, ativo: bool) -> None:
        self.avl.definir_modo_detalhado(ativo)
        self.rn.definir_modo_detalhado(ativo)

    def validar(self) -> tuple[bool, list[str]]:
        """Valida as duas árvores e confere se guardam exatamente as mesmas contas."""
        erros: list[str] = []
        for nome, arvore in (("AVL", self.avl), ("RN", self.rn)):
            ok, violacoes = arvore.validar()
            erros += [f"{nome}: {v}" for v in violacoes]
        if self.avl.em_ordem() != self.rn.em_ordem():
            erros.append("coleção comum: AVL e RN guardam contas diferentes")
        return (not erros, erros)
