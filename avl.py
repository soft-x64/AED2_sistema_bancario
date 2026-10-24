"""Árvore AVL para o Sistema Bancário (AED II).

Responsável: I1 · Revisor: I3

Convenções do grupo (PLANO.md, seção 3):
- Chave = conta.numero (int). Nenhum outro atributo participa da ordenação.
- Altura em arestas: árvore vazia = -1, folha = 0.
- Rotação simples conta 1; rotação dupla (LR/RL) conta 2.
- Nós visitados são contados somente em buscar().
- Remoção de nó com 2 filhos usa o sucessor (mínimo da subárvore direita).

Etapa 1 (este arquivo): nó, busca, inserção com rotações, consultas,
estatísticas e modo detalhado. Remoção, validação e exibição vêm na Etapa 2/3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # só para type hints; a AVL não depende de modelos.py em tempo de execução
    from modelos import Conta


class _NoAVL:
    """Nó interno da AVL. Guarda a conta inteira e a altura da própria subárvore."""

    __slots__ = ("conta", "esquerda", "direita", "altura")

    def __init__(self, conta: Conta) -> None:
        self.conta = conta
        self.esquerda: _NoAVL | None = None
        self.direita: _NoAVL | None = None
        self.altura = 0  # um nó novo é sempre folha


def _altura(no: _NoAVL | None) -> int:
    """Altura de uma subárvore; subárvore vazia vale -1."""
    return no.altura if no is not None else -1


def _fator_balanceamento(no: _NoAVL) -> int:
    """FB = altura(esquerda) - altura(direita). Positivo = pende para a esquerda."""
    return _altura(no.esquerda) - _altura(no.direita)


def _atualizar_altura(no: _NoAVL) -> None:
    no.altura = 1 + max(_altura(no.esquerda), _altura(no.direita))


class ArvoreAVL:
    """Árvore AVL de contas, ordenada pelo número da conta."""

    NOME = "AVL"

    def __init__(self) -> None:
        self._raiz: _NoAVL | None = None
        self._tamanho = 0
        self._detalhado = False
        self._rotacoes = 0
        self._nos_visitados = 0
        self._buscas = 0

    # ------------------------------------------------------------------ #
    # Modo detalhado
    # ------------------------------------------------------------------ #
    def definir_modo_detalhado(self, ativo: bool) -> None:
        self._detalhado = bool(ativo)

    def _log(self, mensagem: str) -> None:
        if self._detalhado:
            print(f"[{self.NOME}] {mensagem}")

    # ------------------------------------------------------------------ #
    # Estatísticas
    # ------------------------------------------------------------------ #
    def estatisticas(self) -> dict:
        return {
            "rotacoes": self._rotacoes,
            "recoloracoes": None,  # não se aplica à AVL
            "nos_visitados": self._nos_visitados,
            "buscas": self._buscas,
        }

    def resetar_estatisticas(self) -> None:
        self._rotacoes = 0
        self._nos_visitados = 0
        self._buscas = 0

    # ------------------------------------------------------------------ #
    # Rotações e rebalanceamento
    # ------------------------------------------------------------------ #
    def _rotacao_direita(self, y: _NoAVL) -> _NoAVL:
        """Rotação simples à direita em y. Retorna a nova raiz da subárvore.

              y               x
             / \\             / \\
            x   C    →      A   y
           / \\                 / \\
          A   B               B   C
        """
        x = y.esquerda
        assert x is not None
        y.esquerda = x.direita
        x.direita = y
        _atualizar_altura(y)  # y desceu: atualiza primeiro
        _atualizar_altura(x)
        self._rotacoes += 1
        self._log(f"rotação à direita em {y.conta.numero} → {x.conta.numero} sobe")
        return x

    def _rotacao_esquerda(self, x: _NoAVL) -> _NoAVL:
        """Rotação simples à esquerda em x (espelho da rotação à direita)."""
        y = x.direita
        assert y is not None
        x.direita = y.esquerda
        y.esquerda = x
        _atualizar_altura(x)
        _atualizar_altura(y)
        self._rotacoes += 1
        self._log(f"rotação à esquerda em {x.conta.numero} → {y.conta.numero} sobe")
        return y

    def _balancear(self, no: _NoAVL) -> _NoAVL:
        """Atualiza a altura de `no` e, se |FB| = 2, aplica o caso adequado.

        Usado na volta da recursão da inserção e (Etapa 2) da remoção.
        O teste `>= 0` / `<= 0` no filho cobre o caso FB(filho) = 0, que só
        ocorre na remoção e se resolve com rotação simples.
        """
        _atualizar_altura(no)
        fb = _fator_balanceamento(no)

        if fb > 1:  # pende para a esquerda
            assert no.esquerda is not None
            if _fator_balanceamento(no.esquerda) >= 0:
                self._log(f"desbalanceado em {no.conta.numero} (FB=+{fb}) → caso LL")
                return self._rotacao_direita(no)
            self._log(f"desbalanceado em {no.conta.numero} (FB=+{fb}) → caso LR")
            no.esquerda = self._rotacao_esquerda(no.esquerda)
            return self._rotacao_direita(no)

        if fb < -1:  # pende para a direita
            assert no.direita is not None
            if _fator_balanceamento(no.direita) <= 0:
                self._log(f"desbalanceado em {no.conta.numero} (FB={fb}) → caso RR")
                return self._rotacao_esquerda(no)
            self._log(f"desbalanceado em {no.conta.numero} (FB={fb}) → caso RL")
            no.direita = self._rotacao_direita(no.direita)
            return self._rotacao_esquerda(no)

        return no

    # ------------------------------------------------------------------ #
    # Busca
    # ------------------------------------------------------------------ #
    def buscar(self, numero: int) -> Conta | None:
        """Busca iterativa. Cada nó real cuja chave é comparada conta 1 visita."""
        self._buscas += 1
        no = self._raiz
        caminho: list[int] = []
        while no is not None:
            self._nos_visitados += 1
            chave = no.conta.numero
            if self._detalhado:
                caminho.append(chave)
            if numero == chave:
                self._log(f"busca {numero}: encontrada · caminho {caminho}")
                return no.conta
            no = no.esquerda if numero < chave else no.direita
        self._log(f"busca {numero}: não encontrada · caminho {caminho}")
        return None

    # ------------------------------------------------------------------ #
    # Inserção
    # ------------------------------------------------------------------ #
    def inserir(self, conta: Conta) -> bool:
        """Insere a conta. Retorna False (sem alterar nada) se o número já existe."""
        self._inseriu = False
        self._raiz = self._inserir(self._raiz, conta, None)
        if self._inseriu:
            self._tamanho += 1
        else:
            self._log(f"inserção {conta.numero}: duplicata rejeitada")
        return self._inseriu

    def _inserir(self, no: _NoAVL | None, conta: Conta, pai: int | None) -> _NoAVL:
        if no is None:
            self._inseriu = True
            onde = "como raiz" if pai is None else f"sob {pai}"
            self._log(f"inserido {conta.numero} {onde}")
            return _NoAVL(conta)

        chave = no.conta.numero
        if conta.numero < chave:
            no.esquerda = self._inserir(no.esquerda, conta, chave)
        elif conta.numero > chave:
            no.direita = self._inserir(no.direita, conta, chave)
        else:
            return no  # duplicata: devolve o nó intacto, nada muda no caminho

        if not self._inseriu:
            return no  # duplicata em nível abaixo: alturas não mudaram
        return self._balancear(no)

    # ------------------------------------------------------------------ #
    # Remoção (Etapa 2)
    # ------------------------------------------------------------------ #
    def remover(self, numero: int) -> Conta | None:
        raise NotImplementedError("Etapa 2")

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #
    def minimo(self) -> Conta | None:
        no = self._raiz
        if no is None:
            return None
        while no.esquerda is not None:
            no = no.esquerda
        return no.conta

    def maximo(self) -> Conta | None:
        no = self._raiz
        if no is None:
            return None
        while no.direita is not None:
            no = no.direita
        return no.conta

    def pre_ordem(self) -> list[Conta]:
        saida: list[Conta] = []
        self._pre(self._raiz, saida)
        return saida

    def em_ordem(self) -> list[Conta]:
        saida: list[Conta] = []
        self._em(self._raiz, saida)
        return saida

    def pos_ordem(self) -> list[Conta]:
        saida: list[Conta] = []
        self._pos(self._raiz, saida)
        return saida

    def _pre(self, no: _NoAVL | None, saida: list[Conta]) -> None:
        if no is not None:
            saida.append(no.conta)
            self._pre(no.esquerda, saida)
            self._pre(no.direita, saida)

    def _em(self, no: _NoAVL | None, saida: list[Conta]) -> None:
        if no is not None:
            self._em(no.esquerda, saida)
            saida.append(no.conta)
            self._em(no.direita, saida)

    def _pos(self, no: _NoAVL | None, saida: list[Conta]) -> None:
        if no is not None:
            self._pos(no.esquerda, saida)
            self._pos(no.direita, saida)
            saida.append(no.conta)

    def altura(self) -> int:
        return _altura(self._raiz)

    def tamanho(self) -> int:
        return self._tamanho

    # ------------------------------------------------------------------ #
    # Exibição e validação (Etapa 3)
    # ------------------------------------------------------------------ #
    def exibir(self) -> str:
        raise NotImplementedError("Etapa 3")

    def validar(self) -> tuple[bool, list[str]]:
        raise NotImplementedError("Etapa 3")