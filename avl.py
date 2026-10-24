"""Árvore AVL para o Sistema Bancário (AED II).

Responsável: I1 · Revisor: I3

Convenções do grupo (PLANO.md, seção 3):
- Chave = conta.numero (int). Nenhum outro atributo participa da ordenação.
- Altura em arestas: árvore vazia = -1, folha = 0.
- Rotação simples conta 1; rotação dupla (LR/RL) conta 2.
- Nós visitados são contados somente em buscar().
- Remoção de nó com 2 filhos usa o sucessor (mínimo da subárvore direita).

Etapa 1: nó, busca, inserção com rotações, consultas, estatísticas, modo detalhado.
Etapa 2: remoção (folha, 1 filho, 2 filhos com sucessor) com rebalanceamento.
Etapa 3: validar() e exibir().
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
    # Remoção
    # ------------------------------------------------------------------ #
    def remover(self, numero: int) -> Conta | None:
        """Remove a conta com esse número e a devolve; None se não existir.

        Chave ausente não altera a árvore nem os contadores.
        """
        self._removida: Conta | None = None
        self._raiz = self._remover(self._raiz, numero)
        if self._removida is None:
            self._log(f"remoção {numero}: não encontrada")
            return None
        self._tamanho -= 1
        return self._removida

    def _remover(self, no: _NoAVL | None, numero: int) -> _NoAVL | None:
        if no is None:
            return None  # chegou ao fim sem achar: nada muda neste caminho

        chave = no.conta.numero
        if numero < chave:
            no.esquerda = self._remover(no.esquerda, numero)
        elif numero > chave:
            no.direita = self._remover(no.direita, numero)
        else:
            # Achou: guarda a conta original antes de qualquer substituição.
            self._removida = no.conta

            # Casos 1 e 2: folha ou um filho → o filho (ou None) sobe no lugar.
            if no.esquerda is None or no.direita is None:
                filho = no.esquerda if no.esquerda is not None else no.direita
                caso = "folha" if filho is None else "1 filho"
                self._log(f"removido {chave} ({caso})")
                return filho

            # Caso 3: dois filhos → o sucessor (mínimo da direita) assume o lugar.
            sucessor = no.direita
            while sucessor.esquerda is not None:
                sucessor = sucessor.esquerda
            self._log(
                f"removido {chave} (2 filhos) → sucessor {sucessor.conta.numero} assume"
            )
            no.conta = sucessor.conta  # a Conta inteira, não só o número
            # Remove o sucessor da subárvore direita. Ele tem no máximo 1 filho
            # (o direito), então essa chamada cai sempre nos casos 1 ou 2.
            no.direita = self._remover_sucessor(no.direita)

        if self._removida is None:
            return no  # chave ausente: alturas não mudaram
        return self._balancear(no)

    def _remover_sucessor(self, no: _NoAVL) -> _NoAVL | None:
        """Remove o nó mínimo da subárvore, rebalanceando na volta."""
        if no.esquerda is None:
            return no.direita
        no.esquerda = self._remover_sucessor(no.esquerda)
        return self._balancear(no)

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
    # Exibição
    # ------------------------------------------------------------------ #
    def exibir(self) -> str:
        """Desenha a árvore deitada: raiz à esquerda, filho direito acima.

        Cada nó aparece como `numero [h=altura, FB=fator]`. Retorna a string;
        quem imprime é o menu.
        """
        if self._raiz is None:
            return "(árvore vazia)"
        linhas: list[str] = []
        self._desenhar(self._raiz, "", "", linhas)
        return "\n".join(linhas)

    def _desenhar(self, no: _NoAVL | None, prefixo: str, conector: str,
                  linhas: list[str]) -> None:
        """Percurso direita → nó → esquerda, para a direita ficar no alto.

        `prefixo` acumula as barras verticais dos níveis de cima; `conector`
        é o ramo que liga este nó ao pai (┌── acima do pai, └── abaixo).
        """
        if no is None:
            return
        # Filho direito: fica acima. A barra vertical só continua para baixo
        # se este nó estiver ABAIXO do pai (└──), ligando-o ao pai.
        if no.direita is not None:
            continua = "│   " if conector == "└── " else "    "
            self._desenhar(no.direita, prefixo + (continua if conector else ""),
                           "┌── ", linhas)

        fb = _fator_balanceamento(no)
        fb_txt = f"{fb:+d}" if fb else "0"
        linhas.append(f"{prefixo}{conector}{no.conta.numero} [h={no.altura}, FB={fb_txt}]")

        if no.esquerda is not None:
            continua = "│   " if conector == "┌── " else "    "
            self._desenhar(no.esquerda, prefixo + (continua if conector else ""),
                           "└── ", linhas)

    # ------------------------------------------------------------------ #
    # Validação
    # ------------------------------------------------------------------ #
    def validar(self) -> tuple[bool, list[str]]:
        """Confere todas as propriedades da AVL sem confiar nos dados guardados.

        Verifica, para cada nó:
        1. Ordem de busca com limites (mín, máx) herdados de TODOS os
           ancestrais — não só pai × filho.
        2. |FB| ≤ 1, com FB calculado a partir das alturas REAIS.
        3. Altura armazenada = altura recalculada.
        E, ao final, tamanho armazenado = número real de nós.

        Retorna (True, []) se tudo estiver certo, ou (False, [violações]).
        Não para no primeiro erro: lista todas as violações encontradas.
        """
        violacoes: list[str] = []
        _, contagem = self._validar(self._raiz, None, None, violacoes)
        if contagem != self._tamanho:
            violacoes.append(
                f"tamanho armazenado {self._tamanho} ≠ número real de nós {contagem}"
            )
        return (not violacoes, violacoes)

    def _validar(self, no: _NoAVL | None, minimo: int | None, maximo: int | None,
                 violacoes: list[str]) -> tuple[int, int]:
        """Retorna (altura real, quantidade de nós) da subárvore."""
        if no is None:
            return -1, 0

        k = no.conta.numero
        if (minimo is not None and k <= minimo) or (maximo is not None and k >= maximo):
            faixa = f"({'-∞' if minimo is None else minimo}, {'+∞' if maximo is None else maximo})"
            violacoes.append(f"ordem violada: {k} fora do intervalo permitido {faixa}")

        # À esquerda, tudo deve ser < k; à direita, tudo > k.
        h_esq, n_esq = self._validar(no.esquerda, minimo, k, violacoes)
        h_dir, n_dir = self._validar(no.direita, k, maximo, violacoes)

        fb_real = h_esq - h_dir
        if abs(fb_real) > 1:
            violacoes.append(f"desbalanceado: nó {k} com FB={fb_real:+d}")

        h_real = 1 + max(h_esq, h_dir)
        if no.altura != h_real:
            violacoes.append(
                f"altura inconsistente: nó {k} guarda h={no.altura}, real h={h_real}"
            )
        return h_real, n_esq + n_dir + 1