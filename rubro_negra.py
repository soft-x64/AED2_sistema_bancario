"""Árvore Rubro-Negra para o Sistema Bancário (AED II).

Responsável: I2 · Revisor: I1

Convenções do grupo (PLANO.md, seção 3):
- Chave = conta.numero (int). Nenhum outro atributo participa da ordenação.
- Altura em arestas: árvore vazia = -1, folha = 0. O NIL não conta.
- NIL: sentinela único por árvore, sempre preto, nunca retornado nem exibido.
- Rotação simples conta 1; o caso triângulo (rotação dupla) conta 2.
- Recoloração conta só se a cor realmente mudou. O nó novo nasce vermelho
  (não conta); pintá-lo de preto ao virar raiz conta.
- Nós visitados são contados somente em buscar(), e só nós reais.
- Remoção de nó com 2 filhos usa o sucessor (mínimo da subárvore direita);
  o nó do sucessor (com a Conta inteira) assume o lugar do removido.
- Implementação iterativa com ponteiro para o pai (estilo CLRS).

Conteúdo: nó, sentinela, busca, inserção e remoção com correções,
consultas, exibição, validação, estatísticas e modo detalhado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # só para type hints; a RN não depende de modelos.py em tempo de execução
    from modelos import Conta


VERMELHO = "V"
PRETO = "P"


class _NoRN:
    """Nó interno da Rubro-Negra. Guarda a conta inteira, a cor e o pai."""

    __slots__ = ("conta", "cor", "esquerda", "direita", "pai")

    def __init__(
        self,
        conta: Conta | None,
        cor: str,
        esquerda: _NoRN | None = None,
        direita: _NoRN | None = None,
        pai: _NoRN | None = None,
    ) -> None:
        self.conta = conta
        self.cor = cor
        # O sentinela é criado com None e depois aponta para si mesmo;
        # todo nó real recebe o NIL da árvore nesses três campos.
        self.esquerda = esquerda
        self.direita = direita
        self.pai = pai


class ArvoreRubroNegra:
    """Árvore Rubro-Negra de contas, ordenada pelo número da conta."""

    NOME = "RN"

    def __init__(self) -> None:
        # Sentinela único desta árvore: preto, sem conta, aponta para si mesmo.
        self.NIL = _NoRN(None, PRETO)
        self.NIL.esquerda = self.NIL.direita = self.NIL.pai = self.NIL
        self._raiz: _NoRN = self.NIL
        self._tamanho = 0
        self._detalhado = False
        self._rotacoes = 0
        self._recoloracoes = 0
        self._nos_visitados = 0
        self._buscas = 0

    # ------------------------------------------------------------------ #
    # Modo detalhado
    # ------------------------------------------------------------------ #
    def definir_modo_detalhado(self, ativo: bool) -> None:
        """Liga ou desliga o passo a passo impresso no terminal."""
        self._detalhado = bool(ativo)

    def _log(self, mensagem: str) -> None:
        if self._detalhado:
            print(f"[{self.NOME}] {mensagem}")

    # ------------------------------------------------------------------ #
    # Estatísticas
    # ------------------------------------------------------------------ #
    def estatisticas(self) -> dict:
        """Contadores desde o último reset."""
        return {
            "rotacoes": self._rotacoes,
            "recoloracoes": self._recoloracoes,
            "nos_visitados": self._nos_visitados,
            "buscas": self._buscas,
        }

    def resetar_estatisticas(self) -> None:
        """Zera os contadores sem mexer na árvore."""
        self._rotacoes = 0
        self._recoloracoes = 0
        self._nos_visitados = 0
        self._buscas = 0

    # ------------------------------------------------------------------ #
    # Cores
    # ------------------------------------------------------------------ #
    def _pintar(self, no: _NoRN, cor: str) -> bool:
        """Única porta de troca de cor: compara antes e só conta se mudou.

        Retorna True se a cor foi alterada.
        """
        if no.cor == cor:
            return False
        no.cor = cor
        self._recoloracoes += 1
        return True

    # ------------------------------------------------------------------ #
    # Rotações
    # ------------------------------------------------------------------ #
    def _rotacao_esquerda(self, x: _NoRN) -> None:
        """Rotação simples à esquerda em x, ajustando os ponteiros de pai.

            x                 y
           / \\               / \\
          A   y      →      x   C
             / \\           / \\
            B   C         A   B
        """
        y = x.direita
        assert y is not self.NIL
        x.direita = y.esquerda
        if y.esquerda is not self.NIL:
            y.esquerda.pai = x
        y.pai = x.pai
        if x.pai is self.NIL:
            self._raiz = y
        elif x is x.pai.esquerda:
            x.pai.esquerda = y
        else:
            x.pai.direita = y
        y.esquerda = x
        x.pai = y
        self._rotacoes += 1
        self._log(
            f"rotação à esquerda em {x.conta.numero} → {y.conta.numero} sobe "
            f"(rotações: {self._rotacoes})"
        )

    def _rotacao_direita(self, y: _NoRN) -> None:
        """Rotação simples à direita em y (espelho da rotação à esquerda)."""
        x = y.esquerda
        assert x is not self.NIL
        y.esquerda = x.direita
        if x.direita is not self.NIL:
            x.direita.pai = y
        x.pai = y.pai
        if y.pai is self.NIL:
            self._raiz = x
        elif y is y.pai.direita:
            y.pai.direita = x
        else:
            y.pai.esquerda = x
        x.direita = y
        y.pai = x
        self._rotacoes += 1
        self._log(
            f"rotação à direita em {y.conta.numero} → {x.conta.numero} sobe "
            f"(rotações: {self._rotacoes})"
        )

    # ------------------------------------------------------------------ #
    # Busca
    # ------------------------------------------------------------------ #
    def buscar(self, numero: int) -> Conta | None:
        """Busca iterativa. Cada nó real cuja chave é comparada conta 1 visita."""
        self._buscas += 1
        no = self._raiz
        caminho: list[int] = []
        while no is not self.NIL:
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
        numero = conta.numero
        pai = self.NIL
        atual = self._raiz
        while atual is not self.NIL:
            pai = atual
            chave = atual.conta.numero
            if numero < chave:
                atual = atual.esquerda
            elif numero > chave:
                atual = atual.direita
            else:
                self._log(f"inserção {numero}: duplicata rejeitada")
                return False

        # Nó novo nasce vermelho (não conta como recoloração).
        novo = _NoRN(conta, VERMELHO, self.NIL, self.NIL, pai)
        if pai is self.NIL:
            self._raiz = novo
            self._log(f"inserido {numero} como raiz")
        else:
            if numero < pai.conta.numero:
                pai.esquerda = novo
            else:
                pai.direita = novo
            self._log(f"inserido {numero} sob {pai.conta.numero}")

        self._tamanho += 1
        self._corrigir_insercao(novo)
        return True

    def _corrigir_insercao(self, z: _NoRN) -> None:
        """Restaura as propriedades após inserir o nó vermelho z.

        Enquanto o pai de z for vermelho (vermelho-vermelho):
        - tio vermelho: pai e tio pretos, avô vermelho; o problema sobe ao avô;
        - tio preto, triângulo: rotação no pai transforma em linha;
        - tio preto, linha: pai preto, avô vermelho e rotação no avô.
        No fim, a raiz é pintada de preto (conta só se mudou).
        """
        while z.pai.cor == VERMELHO:
            pai = z.pai
            avo = pai.pai  # existe: pai vermelho nunca é a raiz
            if pai is avo.esquerda:
                tio = avo.direita
                if tio.cor == VERMELHO:
                    self._caso_tio_vermelho(pai, tio, avo)
                    z = avo
                    continue
                if z is pai.direita:  # triângulo esquerda-direita
                    self._log(
                        f"tio {self._nome(tio)} preto, triângulo (LR) em "
                        f"{z.conta.numero} → rotação dupla"
                    )
                    z = pai
                    self._rotacao_esquerda(z)
                    pai = z.pai
                else:
                    self._log(
                        f"tio {self._nome(tio)} preto, linha (LL) em "
                        f"{z.conta.numero}"
                    )
                self._caso_linha(pai, avo)
                self._rotacao_direita(avo)
            else:  # espelho: pai é filho direito do avô
                tio = avo.esquerda
                if tio.cor == VERMELHO:
                    self._caso_tio_vermelho(pai, tio, avo)
                    z = avo
                    continue
                if z is pai.esquerda:  # triângulo direita-esquerda
                    self._log(
                        f"tio {self._nome(tio)} preto, triângulo (RL) em "
                        f"{z.conta.numero} → rotação dupla"
                    )
                    z = pai
                    self._rotacao_direita(z)
                    pai = z.pai
                else:
                    self._log(
                        f"tio {self._nome(tio)} preto, linha (RR) em "
                        f"{z.conta.numero}"
                    )
                self._caso_linha(pai, avo)
                self._rotacao_esquerda(avo)

        if self._pintar(self._raiz, PRETO):
            self._log(
                f"raiz {self._raiz.conta.numero} pintada de preto "
                f"(recolorações: {self._recoloracoes})"
            )

    def _caso_tio_vermelho(self, pai: _NoRN, tio: _NoRN, avo: _NoRN) -> None:
        self._log(
            f"tio {tio.conta.numero} vermelho → recolorir "
            f"{pai.conta.numero}(P), {tio.conta.numero}(P), {avo.conta.numero}(V)"
        )
        self._pintar(pai, PRETO)
        self._pintar(tio, PRETO)
        self._pintar(avo, VERMELHO)
        self._log(f"recolorações: {self._recoloracoes}")

    def _caso_linha(self, pai: _NoRN, avo: _NoRN) -> None:
        self._log(
            f"recolorir {pai.conta.numero}(P), {avo.conta.numero}(V) "
            f"e rotacionar em {avo.conta.numero}"
        )
        self._pintar(pai, PRETO)
        self._pintar(avo, VERMELHO)

    def _nome(self, no: _NoRN) -> str:
        """Rótulo de um nó para o modo detalhado (o NIL aparece como 'NIL')."""
        return "NIL" if no is self.NIL else str(no.conta.numero)

    # ------------------------------------------------------------------ #
    # Remoção
    # ------------------------------------------------------------------ #
    def _localizar(self, numero: int) -> _NoRN:
        """Nó com a chave, ou NIL. Não conta nós visitados (só buscar() conta)."""
        no = self._raiz
        while no is not self.NIL:
            chave = no.conta.numero
            if numero == chave:
                return no
            no = no.esquerda if numero < chave else no.direita
        return self.NIL

    def _transplantar(self, u: _NoRN, v: _NoRN) -> None:
        """Coloca a subárvore v no lugar de u, ligando v ao pai de u.

        Atualiza v.pai mesmo quando v é o NIL: a correção da remoção usa
        esse ponteiro para saber onde está o "preto duplo".
        """
        if u.pai is self.NIL:
            self._raiz = v
        elif u is u.pai.esquerda:
            u.pai.esquerda = v
        else:
            u.pai.direita = v
        v.pai = u.pai

    def remover(self, numero: int) -> Conta | None:
        """Remove e retorna a conta com o número dado; None se não existir.

        - folha ou 1 filho: o filho (ou NIL) sobe para o lugar do nó;
        - 2 filhos: o sucessor y sai da sua posição e assume o lugar de z,
          herdando a cor de z (conta como recoloração só se a cor mudou).
        Se a cor que saiu da árvore era preta, há um "preto duplo" em x e
        a correção é chamada.
        """
        z = self._localizar(numero)
        if z is self.NIL:
            self._log(f"remoção {numero}: não encontrada")
            return None

        y = z
        cor_original_y = y.cor
        if z.esquerda is self.NIL:
            if z.direita is self.NIL:
                self._log(f"remover {numero}: folha ({'V' if z.cor == VERMELHO else 'P'})")
            else:
                self._log(f"remover {numero}: 1 filho (direito) → sobe para o lugar")
            x = z.direita
            self._transplantar(z, z.direita)
        elif z.direita is self.NIL:
            self._log(f"remover {numero}: 1 filho (esquerdo) → sobe para o lugar")
            x = z.esquerda
            self._transplantar(z, z.esquerda)
        else:
            y = self._minimo_no(z.direita)
            self._log(
                f"remover {numero}: 2 filhos → sucessor {y.conta.numero} assume o lugar"
            )
            cor_original_y = y.cor
            x = y.direita
            if y.pai is z:
                x.pai = y  # necessário quando x é o NIL
            else:
                self._transplantar(y, y.direita)
                y.direita = z.direita
                y.direita.pai = y
            self._transplantar(z, y)
            y.esquerda = z.esquerda
            y.esquerda.pai = y
            if self._pintar(y, z.cor):
                self._log(
                    f"sucessor {y.conta.numero} herda a cor de {numero} "
                    f"(recolorações: {self._recoloracoes})"
                )

        self._tamanho -= 1
        if cor_original_y == PRETO:
            self._corrigir_remocao(x)
        self.NIL.pai = self.NIL  # devolve o sentinela ao estado neutro
        return z.conta

    def _corrigir_remocao(self, x: _NoRN) -> None:
        """Elimina o "preto duplo" em x (que pode ser o NIL).

        Com x filho esquerdo e w seu irmão (os espelhos trocam os lados):
        - caso 1, irmão vermelho: w preto, pai vermelho, rotação no pai;
          vira um dos casos 2, 3 ou 4;
        - caso 2, irmão preto com filhos pretos: w vermelho e o problema
          sobe para o pai (termina se o pai for vermelho ou a raiz);
        - caso 3, sobrinho próximo vermelho e distante preto: rotação em w
          transforma no caso 4;
        - caso 4, sobrinho distante vermelho: w herda a cor do pai, pai e
          sobrinho distante pretos, rotação no pai; termina.
        No fim, x é pintado de preto (conta só se mudou).
        """
        while x is not self._raiz and x.cor == PRETO:
            pai = x.pai
            if x is pai.esquerda:
                w = pai.direita
                if w.cor == VERMELHO:
                    self._log(
                        f"caso 1: irmão {w.conta.numero} vermelho → recolorir "
                        f"{w.conta.numero}(P), {pai.conta.numero}(V) e rotacionar "
                        f"em {pai.conta.numero}"
                    )
                    self._pintar(w, PRETO)
                    self._pintar(pai, VERMELHO)
                    self._rotacao_esquerda(pai)
                    w = pai.direita
                if w.esquerda.cor == PRETO and w.direita.cor == PRETO:
                    self._caso_irmao_filhos_pretos(w, pai)
                    x = pai
                    continue
                if w.direita.cor == PRETO:  # caso 3: sobrinho próximo vermelho
                    self._log(
                        f"caso 3: sobrinho próximo {w.esquerda.conta.numero} vermelho "
                        f"→ recolorir {w.esquerda.conta.numero}(P), "
                        f"{w.conta.numero}(V) e rotacionar em {w.conta.numero}"
                    )
                    self._pintar(w.esquerda, PRETO)
                    self._pintar(w, VERMELHO)
                    self._rotacao_direita(w)
                    w = pai.direita
                self._caso_sobrinho_distante(w, pai, w.direita)
                self._rotacao_esquerda(pai)
                x = self._raiz
            else:  # espelho: x é filho direito
                w = pai.esquerda
                if w.cor == VERMELHO:
                    self._log(
                        f"caso 1 (espelho): irmão {w.conta.numero} vermelho → "
                        f"recolorir {w.conta.numero}(P), {pai.conta.numero}(V) e "
                        f"rotacionar em {pai.conta.numero}"
                    )
                    self._pintar(w, PRETO)
                    self._pintar(pai, VERMELHO)
                    self._rotacao_direita(pai)
                    w = pai.esquerda
                if w.esquerda.cor == PRETO and w.direita.cor == PRETO:
                    self._caso_irmao_filhos_pretos(w, pai)
                    x = pai
                    continue
                if w.esquerda.cor == PRETO:  # caso 3 (espelho)
                    self._log(
                        f"caso 3 (espelho): sobrinho próximo "
                        f"{w.direita.conta.numero} vermelho → recolorir "
                        f"{w.direita.conta.numero}(P), {w.conta.numero}(V) e "
                        f"rotacionar em {w.conta.numero}"
                    )
                    self._pintar(w.direita, PRETO)
                    self._pintar(w, VERMELHO)
                    self._rotacao_esquerda(w)
                    w = pai.esquerda
                self._caso_sobrinho_distante(w, pai, w.esquerda)
                self._rotacao_direita(pai)
                x = self._raiz

        if self._pintar(x, PRETO):
            self._log(
                f"{x.conta.numero} pintado de preto "
                f"(recolorações: {self._recoloracoes})"
            )

    def _caso_irmao_filhos_pretos(self, w: _NoRN, pai: _NoRN) -> None:
        self._log(
            f"caso 2: irmão {w.conta.numero} preto com filhos pretos → "
            f"recolorir {w.conta.numero}(V), problema sobe para {pai.conta.numero}"
        )
        self._pintar(w, VERMELHO)

    def _caso_sobrinho_distante(self, w: _NoRN, pai: _NoRN, distante: _NoRN) -> None:
        self._log(
            f"caso 4: sobrinho distante {distante.conta.numero} vermelho → "
            f"{w.conta.numero} herda a cor de {pai.conta.numero}, "
            f"{pai.conta.numero}(P), {distante.conta.numero}(P) e rotacionar "
            f"em {pai.conta.numero}"
        )
        self._pintar(w, pai.cor)
        self._pintar(pai, PRETO)
        self._pintar(distante, PRETO)

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #
    def _minimo_no(self, no: _NoRN) -> _NoRN:
        while no.esquerda is not self.NIL:
            no = no.esquerda
        return no

    def minimo(self) -> Conta | None:
        if self._raiz is self.NIL:
            return None
        return self._minimo_no(self._raiz).conta

    def maximo(self) -> Conta | None:
        no = self._raiz
        if no is self.NIL:
            return None
        while no.direita is not self.NIL:
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

    def _pre(self, no: _NoRN, saida: list[Conta]) -> None:
        if no is not self.NIL:
            saida.append(no.conta)
            self._pre(no.esquerda, saida)
            self._pre(no.direita, saida)

    def _em(self, no: _NoRN, saida: list[Conta]) -> None:
        if no is not self.NIL:
            self._em(no.esquerda, saida)
            saida.append(no.conta)
            self._em(no.direita, saida)

    def _pos(self, no: _NoRN, saida: list[Conta]) -> None:
        if no is not self.NIL:
            self._pos(no.esquerda, saida)
            self._pos(no.direita, saida)
            saida.append(no.conta)

    def altura(self) -> int:
        """Altura em arestas (vazia = -1, folha = 0); o NIL não conta."""
        return self._altura(self._raiz)

    def _altura(self, no: _NoRN) -> int:
        if no is self.NIL:
            return -1
        return 1 + max(self._altura(no.esquerda), self._altura(no.direita))

    def tamanho(self) -> int:
        return self._tamanho

    # ------------------------------------------------------------------ #
    # Exibição
    # ------------------------------------------------------------------ #
    def exibir(self) -> str:
        """Árvore deitada: raiz à esquerda, filho direito acima. Ex.: `30 (P)`."""
        if self._raiz is self.NIL:
            return "(árvore vazia)"
        linhas: list[str] = []
        self._exibir(self._raiz, 0, linhas)
        return "\n".join(linhas)

    def _exibir(self, no: _NoRN, nivel: int, linhas: list[str]) -> None:
        if no is self.NIL:
            return
        self._exibir(no.direita, nivel + 1, linhas)
        linhas.append(f"{'    ' * nivel}{no.conta.numero} ({no.cor})")
        self._exibir(no.esquerda, nivel + 1, linhas)

    # ------------------------------------------------------------------ #
    # Validação
    # ------------------------------------------------------------------ #
    def validar(self) -> tuple[bool, list[str]]:
        """Confere todas as propriedades da RN.

        - ordem com limites (mín, máx) propagados por toda a subárvore;
        - raiz preta e NIL preto;
        - nenhum vermelho com filho vermelho;
        - mesma altura negra em todos os caminhos;
        - ponteiros de pai consistentes;
        - tamanho armazenado = contagem real.
        """
        violacoes: list[str] = []

        if self.NIL.cor != PRETO:
            violacoes.append("NIL não é preto")
        if self._raiz is not self.NIL:
            if self._raiz.cor != PRETO:
                violacoes.append(f"raiz {self._raiz.conta.numero} não é preta")
            if self._raiz.pai is not self.NIL:
                violacoes.append(f"raiz {self._raiz.conta.numero} tem pai diferente de NIL")

        _, contagem = self._validar_no(self._raiz, None, None, violacoes)
        if contagem != self._tamanho:
            violacoes.append(
                f"tamanho armazenado {self._tamanho} ≠ contagem real {contagem}"
            )
        return (not violacoes, violacoes)

    def _validar_no(
        self,
        no: _NoRN,
        minimo: int | None,
        maximo: int | None,
        violacoes: list[str],
    ) -> tuple[int, int]:
        """Retorna (altura negra, quantidade de nós reais) da subárvore."""
        if no is self.NIL:
            return 0, 0

        k = no.conta.numero
        if (minimo is not None and k <= minimo) or (maximo is not None and k >= maximo):
            violacoes.append(f"ordem violada em {k} (limites {minimo}, {maximo})")
        if no.cor not in (VERMELHO, PRETO):
            violacoes.append(f"cor inválida em {k}: {no.cor!r}")

        for filho in (no.esquerda, no.direita):
            if filho is self.NIL:
                continue
            if filho.pai is not no:
                violacoes.append(f"pai de {filho.conta.numero} não aponta para {k}")
            if no.cor == VERMELHO and filho.cor == VERMELHO:
                violacoes.append(f"vermelho-vermelho entre {k} e {filho.conta.numero}")

        ae, ce = self._validar_no(no.esquerda, minimo, k, violacoes)
        ad, cd = self._validar_no(no.direita, k, maximo, violacoes)
        if ae != ad:
            violacoes.append(f"altura negra diferente em {k} (esq={ae}, dir={ad})")
        altura_negra = max(ae, ad) + (1 if no.cor == PRETO else 0)
        return altura_negra, ce + cd + 1
