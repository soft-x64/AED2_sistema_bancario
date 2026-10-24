"""Testes da Rubro-Negra (busca, inserção, remoção, correções, consultas,
exibição, validação, estatísticas e modo detalhado).

Os valores esperados dos contadores foram conferidos à mão seguindo as
convenções do PLANO.md (seção 3): o nó novo nasce vermelho e não conta;
recoloração só conta quando a cor muda; pintar a raiz de preto conta;
o caso triângulo soma 2 rotações.
"""

import contextlib
import io
import math
import random
import unittest

from auxiliares import chaves, conta
from rubro_negra import PRETO, VERMELHO, ArvoreRubroNegra, _NoRN

P, V = PRETO, VERMELHO


def arvore_com(*numeros: int) -> ArvoreRubroNegra:
    a = ArvoreRubroNegra()
    for n in numeros:
        a.inserir(conta(n))
    return a


def cores(arvore: ArvoreRubroNegra) -> list[tuple[int, str]]:
    """(número, cor) em pré-ordem, lido direto dos nós."""
    saida = []

    def visitar(no):
        if no is arvore.NIL:
            return
        saida.append((no.conta.numero, no.cor))
        visitar(no.esquerda)
        visitar(no.direita)

    visitar(arvore._raiz)
    return saida


def no_de(arvore: ArvoreRubroNegra, numero: int):
    """Nó interno com a chave dada (para os testes que corrompem a árvore)."""
    no = arvore._raiz
    while no is not arvore.NIL and no.conta.numero != numero:
        no = no.esquerda if numero < no.conta.numero else no.direita
    assert no is not arvore.NIL, f"{numero} não está na árvore"
    return no


def montar(estrutura) -> ArvoreRubroNegra:
    """Monta uma RN nó a nó, com cores escolhidas, para isolar um caso.

    `estrutura` é (chave, cor) ou (chave, cor, esquerda, direita), com None
    para filho ausente. Os contadores começam zerados e a árvore é conferida.
    """
    a = ArvoreRubroNegra()
    total = 0

    def criar(item, pai):
        nonlocal total
        if item is None:
            return a.NIL
        k, cor, esq, dir_ = (tuple(item) + (None, None))[:4]
        no = _NoRN(conta(k), cor, a.NIL, a.NIL, pai)
        no.esquerda = criar(esq, no)
        no.direita = criar(dir_, no)
        total += 1
        return no

    a._raiz = criar(estrutura, a.NIL)
    a._tamanho = total
    verificar_rn(a)
    return a


def verificar_rn(arvore: ArvoreRubroNegra) -> tuple[int, int]:
    """Confere a RN por conta própria, sem usar validar().

    Lança AssertionError se algo estiver errado. Retorna (altura, tamanho) reais.
    """
    nil = arvore.NIL
    assert nil.cor == PRETO, "NIL não é preto"
    raiz = arvore._raiz
    if raiz is not nil:
        assert raiz.cor == PRETO, "raiz não é preta"
        assert raiz.pai is nil, "pai da raiz não é o NIL"

    def visitar(no, minimo, maximo):
        """Retorna (altura em arestas, altura negra, tamanho)."""
        if no is nil:
            return -1, 0, 0
        k = no.conta.numero
        assert (minimo is None or k > minimo) and (maximo is None or k < maximo), (
            f"ordem violada em {k} (limites {minimo}, {maximo})"
        )
        for filho in (no.esquerda, no.direita):
            if filho is not nil:
                assert filho.pai is no, f"pai inconsistente em {filho.conta.numero}"
                assert not (no.cor == VERMELHO and filho.cor == VERMELHO), (
                    f"vermelho-vermelho em {k}"
                )
        he, ne, te = visitar(no.esquerda, minimo, k)
        hd, nd, td = visitar(no.direita, k, maximo)
        assert ne == nd, f"altura negra diferente em {k}"
        return 1 + max(he, hd), ne + (no.cor == PRETO), te + td + 1

    altura, _, tamanho = visitar(raiz, None, None)
    assert arvore.altura() == altura, "altura() diverge da contagem real"
    assert arvore.tamanho() == tamanho, "tamanho() diverge da contagem real"
    return altura, tamanho


class TestCasosBasicos(unittest.TestCase):
    """Casos da tabela do PLANO.md (seção 8, I2)."""

    def test_inserir_10(self):
        a = arvore_com(10)
        self.assertEqual(cores(a), [(10, PRETO)])
        e = a.estatisticas()
        self.assertEqual(e["recoloracoes"], 1)  # vermelho → preto ao virar raiz
        self.assertEqual(e["rotacoes"], 0)
        verificar_rn(a)

    def _conferir_tres(self, sequencia, rotacoes):
        a = arvore_com(*sequencia)
        self.assertEqual(cores(a), [(20, PRETO), (10, VERMELHO), (30, VERMELHO)])
        e = a.estatisticas()
        self.assertEqual(e["rotacoes"], rotacoes)
        self.assertEqual(e["recoloracoes"], 3)  # raiz 10(P) + pai(P) + avô(V)
        self.assertEqual(a.altura(), 1)
        verificar_rn(a)

    def test_linha_rr(self):
        self._conferir_tres([10, 20, 30], 1)

    def test_linha_ll(self):
        self._conferir_tres([30, 20, 10], 1)

    def test_triangulo_rl(self):
        self._conferir_tres([10, 30, 20], 2)

    def test_triangulo_lr(self):
        self._conferir_tres([30, 10, 20], 2)

    def test_sem_correcao(self):
        a = arvore_com(20, 10, 30)
        e = a.estatisticas()
        self.assertEqual((e["rotacoes"], e["recoloracoes"]), (0, 1))


class TestCasosIsolados(unittest.TestCase):
    """Cada caso de correção num ponto interno, com contadores zerados antes."""

    def _base(self, *numeros):
        a = arvore_com(*numeros)
        verificar_rn(a)
        a.resetar_estatisticas()
        return a

    def _contadores(self, a):
        e = a.estatisticas()
        return e["rotacoes"], e["recoloracoes"]

    def test_tio_vermelho_sem_chegar_na_raiz(self):
        # 20P; 10P(5V, 15V); 30P → inserir 1: tio 15 vermelho
        a = self._base(20, 10, 30, 5, 15)
        a.inserir(conta(1))
        self.assertEqual(self._contadores(a), (0, 3))  # 5(P), 15(P), 10(V)
        self.assertEqual(
            cores(a),
            [(20, PRETO), (10, VERMELHO), (5, PRETO), (1, VERMELHO),
             (15, PRETO), (30, PRETO)],
        )
        verificar_rn(a)

    def test_tio_vermelho_chegando_na_raiz(self):
        a = self._base(20, 10, 30)
        a.inserir(conta(5))
        # 10(P), 30(P), 20(V) e a raiz 20 volta a preto → 4
        self.assertEqual(self._contadores(a), (0, 4))
        self.assertEqual(cores(a)[0], (20, PRETO))
        verificar_rn(a)

    def test_linha_ll_interna(self):
        # 20P; 10P(5V); 30P → inserir 1
        a = self._base(20, 10, 30, 5)
        a.inserir(conta(1))
        self.assertEqual(self._contadores(a), (1, 2))  # 5(P), 10(V) + rotação
        self.assertEqual(chaves(a.pre_ordem()), [20, 5, 1, 10, 30])
        verificar_rn(a)

    def test_triangulo_lr_interno(self):
        a = self._base(20, 10, 30, 5)
        a.inserir(conta(7))
        self.assertEqual(self._contadores(a), (2, 2))  # 7(P), 10(V) + dupla
        self.assertEqual(chaves(a.pre_ordem()), [20, 7, 5, 10, 30])
        verificar_rn(a)

    def test_linha_rr_interna(self):
        # 20P; 10P; 30P(35V) → inserir 40
        a = self._base(20, 10, 30, 35)
        a.inserir(conta(40))
        self.assertEqual(self._contadores(a), (1, 2))
        self.assertEqual(chaves(a.pre_ordem()), [20, 10, 35, 30, 40])
        verificar_rn(a)

    def test_triangulo_rl_interno(self):
        a = self._base(20, 10, 30, 35)
        a.inserir(conta(33))
        self.assertEqual(self._contadores(a), (2, 2))
        self.assertEqual(chaves(a.pre_ordem()), [20, 10, 33, 30, 35])
        verificar_rn(a)

    def test_tio_vermelho_propaga_e_rotaciona(self):
        # 20P; 10V(5P(1V, 7V), 15P); 30P → inserir 6:
        # tio 1 vermelho em 7 → 7(P), 1(P), 5(V); sobe para 5, cujo pai 10 é
        # vermelho com tio 30 preto → linha LL: 10(P), 20(V) + rotação em 20.
        a = self._base(20, 10, 30, 5, 15, 1, 7)
        a.inserir(conta(6))
        self.assertEqual(self._contadores(a), (1, 5))
        self.assertEqual(
            cores(a),
            [(10, PRETO), (5, VERMELHO), (1, PRETO), (7, PRETO), (6, VERMELHO),
             (20, VERMELHO), (15, PRETO), (30, PRETO)],
        )
        verificar_rn(a)


class TestInsercao(unittest.TestCase):
    def test_duplicata_rejeitada_sem_sobrescrever(self):
        a = ArvoreRubroNegra()
        original = conta(10, titular="Ana")
        self.assertTrue(a.inserir(original))
        self.assertFalse(a.inserir(conta(10, titular="Bruno")))
        self.assertEqual(a.tamanho(), 1)
        self.assertIs(a.buscar(10), original)

    def test_duplicata_profunda_nao_altera_nada(self):
        a = arvore_com(20, 10, 30, 5, 15, 1)
        antes_cores = cores(a)
        antes_est = a.estatisticas()
        self.assertFalse(a.inserir(conta(1)))
        self.assertEqual(cores(a), antes_cores)
        self.assertEqual(a.estatisticas(), antes_est)
        self.assertEqual(a.tamanho(), 6)
        verificar_rn(a)

    def test_crescente_respeita_limite_de_altura(self):
        n = 1023
        a = arvore_com(*range(1, n + 1))
        altura, tamanho = verificar_rn(a)
        self.assertEqual(tamanho, n)
        self.assertLessEqual(altura, 2 * math.log2(n + 1))
        self.assertEqual(a.validar(), (True, []))

    def test_insercao_nao_conta_nos_visitados(self):
        a = arvore_com(5, 3, 8, 1)
        e = a.estatisticas()
        self.assertEqual((e["nos_visitados"], e["buscas"]), (0, 0))


class TestRemocaoSemCorrecao(unittest.TestCase):
    """Remoções que não geram preto duplo (ou só pintam o filho que sobe)."""

    def _contadores(self, a):
        e = a.estatisticas()
        return e["rotacoes"], e["recoloracoes"]

    def test_folha_vermelha(self):
        a = montar((20, P, (10, V), (30, V)))
        self.assertEqual(a.remover(10).numero, 10)
        self.assertEqual(self._contadores(a), (0, 0))
        self.assertEqual(cores(a), [(20, P), (30, V)])
        verificar_rn(a)

    def test_preto_com_um_filho_vermelho(self):
        # o filho 5 sobe e é pintado de preto → 1 recoloração
        a = montar((20, P, (10, P, (5, V), None), (30, P)))
        a.remover(10)
        self.assertEqual(self._contadores(a), (0, 1))
        self.assertEqual(cores(a), [(20, P), (5, P), (30, P)])
        verificar_rn(a)

    def test_dois_filhos_sucessor_vermelho_distante(self):
        # sucessor 25 (vermelho, não é filho direto) assume o lugar e herda o
        # preto de 20 → 1 recoloração; cor removida foi vermelha, sem correção
        a = montar((20, P, (10, P), (30, P, (25, V), (35, V))))
        a.remover(20)
        self.assertEqual(self._contadores(a), (0, 1))
        self.assertEqual(cores(a), [(25, P), (10, P), (30, P), (35, V)])
        verificar_rn(a)

    def test_dois_filhos_sucessor_filho_direto(self):
        # sucessor 30 é filho direto e já é preto (herdar a cor não conta);
        # saiu um preto: x = 35 vermelho é pintado de preto → 1 recoloração
        a = montar((20, P, (10, P), (30, P, None, (35, V))))
        a.remover(20)
        self.assertEqual(self._contadores(a), (0, 1))
        self.assertEqual(cores(a), [(30, P), (10, P), (35, P)])
        verificar_rn(a)

    def test_dois_filhos_leva_a_conta_inteira(self):
        a = ArvoreRubroNegra()
        sucessor = conta(25, titular="Carla Souza", agencia="0042",
                         tipo="POUPANCA")
        for c in (conta(20), conta(10), conta(30), sucessor, conta(35)):
            a.inserir(c)
        removida = a.remover(20)
        self.assertEqual(removida.numero, 20)
        self.assertIs(a.buscar(25), sucessor)  # mesmo objeto, atributos intactos
        self.assertIsNone(a.buscar(20))
        verificar_rn(a)


class TestRemocaoCorrecao(unittest.TestCase):
    """Os quatro casos da correção (preto duplo) e os espelhos, isolados."""

    def _remover(self, estrutura, numero):
        a = montar(estrutura)
        self.assertEqual(a.remover(numero).numero, numero)
        verificar_rn(a)
        e = a.estatisticas()
        return a, (e["rotacoes"], e["recoloracoes"])

    # caso 1: irmão vermelho → vira caso 2 com pai vermelho
    def test_caso1_irmao_vermelho(self):
        # 30(P), 20(V), rot. esq. em 20; caso 2: 25(V); x=20 vermelho → 20(P)
        a, cont = self._remover((20, P, (10, P), (30, V, (25, P), (35, P))), 10)
        self.assertEqual(cont, (1, 4))
        self.assertEqual(cores(a), [(30, P), (20, P), (25, V), (35, P)])

    def test_caso1_espelho(self):
        a, cont = self._remover((20, P, (10, V, (5, P), (15, P)), (30, P)), 30)
        self.assertEqual(cont, (1, 4))
        self.assertEqual(cores(a), [(10, P), (5, P), (20, P), (15, V)])

    # caso 2: irmão preto com filhos pretos
    def test_caso2_sobe_ate_a_raiz(self):
        a, cont = self._remover((20, P, (10, P), (30, P)), 10)
        self.assertEqual(cont, (0, 1))  # só 30(V); a raiz já é preta
        self.assertEqual(cores(a), [(20, P), (30, V)])

    def test_caso2_espelho(self):
        a, cont = self._remover((20, P, (10, P), (30, P)), 30)
        self.assertEqual(cont, (0, 1))
        self.assertEqual(cores(a), [(20, P), (10, V)])

    def test_caso2_para_no_pai_vermelho(self):
        # 15(V); x sobe para 10, que é vermelho → 10(P)
        a, cont = self._remover((20, P, (10, V, (5, P), (15, P)), (30, P)), 5)
        self.assertEqual(cont, (0, 2))
        self.assertEqual(cores(a), [(20, P), (10, P), (15, V), (30, P)])

    def test_caso2_propaga_por_dois_niveis(self):
        # 3(V); sobe para 2 (preto) → irmão 6 com filhos pretos: 6(V); chega na raiz
        perfeita = (4, P, (2, P, (1, P), (3, P)), (6, P, (5, P), (7, P)))
        a, cont = self._remover(perfeita, 1)
        self.assertEqual(cont, (0, 2))
        self.assertEqual(
            cores(a), [(4, P), (2, P), (3, V), (6, V), (5, P), (7, P)]
        )

    # caso 3: sobrinho próximo vermelho, distante preto → vira caso 4
    def test_caso3_sobrinho_proximo(self):
        # 25(P), 30(V), rot. dir. em 30; caso 4: 30(P), rot. esq. em 20
        a, cont = self._remover((20, P, (10, P), (30, P, (25, V), None)), 10)
        self.assertEqual(cont, (2, 3))
        self.assertEqual(cores(a), [(25, P), (20, P), (30, P)])

    def test_caso3_espelho(self):
        a, cont = self._remover((20, P, (10, P, None, (15, V)), (30, P)), 30)
        self.assertEqual(cont, (2, 3))
        self.assertEqual(cores(a), [(15, P), (10, P), (20, P)])

    def test_caso3_com_pai_vermelho(self):
        # caso 3: 13(P), 15(V), rot. dir. em 15; caso 4: 13 herda o V de 10,
        # 10(P), 15(P), rot. esq. em 10 → 2 rotações e 5 recolorações
        a, cont = self._remover(
            (20, P, (10, V, (5, P), (15, P, (13, V), None)), (30, P)), 5
        )
        self.assertEqual(cont, (2, 5))
        self.assertEqual(
            cores(a), [(20, P), (13, V), (10, P), (15, P), (30, P)]
        )

    def test_caso3_espelho_com_pai_vermelho(self):
        a, cont = self._remover(
            (20, P, (10, P), (30, V, (25, P, None, (27, V)), (35, P))), 35
        )
        self.assertEqual(cont, (2, 5))
        self.assertEqual(
            cores(a), [(20, P), (10, P), (27, V), (25, P), (30, P)]
        )

    # caso 4: sobrinho distante vermelho
    def test_caso4_sobrinho_distante(self):
        # 35(P) e rot. esq. em 20 (30 e 20 já tinham a cor final)
        a, cont = self._remover((20, P, (10, P), (30, P, None, (35, V))), 10)
        self.assertEqual(cont, (1, 1))
        self.assertEqual(cores(a), [(30, P), (20, P), (35, P)])

    def test_caso4_espelho(self):
        a, cont = self._remover((20, P, (10, P, (5, V), None), (30, P)), 30)
        self.assertEqual(cont, (1, 1))
        self.assertEqual(cores(a), [(10, P), (5, P), (20, P)])

    def test_caso4_com_pai_vermelho(self):
        # 15 herda o vermelho de 10, 10(P), 17(P) e rot. esq. em 10 → 3 recolorações
        a, cont = self._remover(
            (20, P, (10, V, (5, P), (15, P, None, (17, V))), (30, P)), 5
        )
        self.assertEqual(cont, (1, 3))
        self.assertEqual(
            cores(a), [(20, P), (15, V), (10, P), (17, P), (30, P)]
        )


class TestRemocaoBordas(unittest.TestCase):
    def test_vazia(self):
        a = ArvoreRubroNegra()
        self.assertIsNone(a.remover(1))
        self.assertEqual((a.altura(), a.tamanho()), (-1, 0))

    def test_inexistente_nao_altera_nada(self):
        a = arvore_com(20, 10, 30, 5, 15, 1)
        antes_cores, antes_est = cores(a), a.estatisticas()
        self.assertIsNone(a.remover(99))
        self.assertIsNone(a.remover(12))
        self.assertEqual(cores(a), antes_cores)
        self.assertEqual(a.estatisticas(), antes_est)
        self.assertEqual(a.tamanho(), 6)

    def test_raiz(self):
        a = arvore_com(20, 10, 30, 5, 15, 25, 35)
        self.assertEqual(a.remover(20).numero, 20)
        verificar_rn(a)
        self.assertEqual(a.tamanho(), 6)
        self.assertNotIn(20, chaves(a.em_ordem()))

    def test_ultimo_no(self):
        a = arvore_com(10)
        a.resetar_estatisticas()
        self.assertEqual(a.remover(10).numero, 10)
        self.assertEqual((a.altura(), a.tamanho()), (-1, 0))
        self.assertIs(a._raiz, a.NIL)
        self.assertEqual(a.exibir(), "(árvore vazia)")
        self.assertEqual(a.estatisticas()["recoloracoes"], 0)
        self.assertEqual(a.validar(), (True, []))
        # a árvore continua usável depois de esvaziar
        self.assertTrue(a.inserir(conta(7)))
        verificar_rn(a)

    def test_esvaziar_em_ordem_aleatoria(self):
        rng = random.Random(7)
        numeros = list(range(1, 301))
        rng.shuffle(numeros)
        a = arvore_com(*numeros)
        rng.shuffle(numeros)
        for i, k in enumerate(numeros, start=1):
            self.assertEqual(a.remover(k).numero, k)
            verificar_rn(a)
            self.assertEqual(a.tamanho(), 300 - i)
        self.assertIs(a._raiz, a.NIL)

    def test_remocao_nao_conta_nos_visitados(self):
        a = arvore_com(5, 3, 8, 1)
        a.remover(3)
        a.remover(42)
        e = a.estatisticas()
        self.assertEqual((e["nos_visitados"], e["buscas"]), (0, 0))

    def test_sentinela_volta_ao_estado_neutro(self):
        a = arvore_com(20, 10, 30)
        a.remover(10)
        self.assertIs(a.NIL.pai, a.NIL)
        self.assertIsNone(a.NIL.conta)
        self.assertEqual(a.NIL.cor, PRETO)


class TestAleatorio(unittest.TestCase):
    def test_2000_operacoes_contra_referencia(self):
        # inserções, remoções e buscas contra um dict, validando a cada passo
        rng = random.Random(2026)
        a, referencia = ArvoreRubroNegra(), {}
        for _ in range(2000):
            k = rng.randint(1, 500)
            operacao = rng.random()
            if operacao < 0.5:
                c = conta(k)
                self.assertEqual(a.inserir(c), k not in referencia)
                referencia.setdefault(k, c)
            elif operacao < 0.85:
                self.assertIs(a.remover(k), referencia.pop(k, None))
            else:
                self.assertIs(a.buscar(k), referencia.get(k))
            verificar_rn(a)
            ok, violacoes = a.validar()
            self.assertTrue(ok, violacoes)
            self.assertEqual(a.tamanho(), len(referencia))
        self.assertEqual(chaves(a.em_ordem()), sorted(referencia))


class TestBusca(unittest.TestCase):
    def test_contagem_so_de_nos_reais(self):
        a = arvore_com(20, 10, 30)
        self.assertEqual(a.buscar(10).numero, 10)   # visita 20, 10
        self.assertIsNone(a.buscar(25))             # visita 20, 30 (NIL não conta)
        e = a.estatisticas()
        self.assertEqual(e["nos_visitados"], 4)
        self.assertEqual(e["buscas"], 2)

    def test_busca_em_vazia(self):
        a = ArvoreRubroNegra()
        self.assertIsNone(a.buscar(1))
        e = a.estatisticas()
        self.assertEqual((e["nos_visitados"], e["buscas"]), (0, 1))

    def test_resetar_estatisticas(self):
        a = arvore_com(30, 20, 10)
        a.buscar(10)
        a.resetar_estatisticas()
        self.assertEqual(
            a.estatisticas(),
            {"rotacoes": 0, "recoloracoes": 0, "nos_visitados": 0, "buscas": 0},
        )
        self.assertEqual(a.tamanho(), 3)  # reset não mexe na árvore


class TestConsultas(unittest.TestCase):
    def test_arvore_vazia(self):
        a = ArvoreRubroNegra()
        self.assertIsNone(a.minimo())
        self.assertIsNone(a.maximo())
        self.assertEqual(a.pre_ordem(), [])
        self.assertEqual(a.em_ordem(), [])
        self.assertEqual(a.pos_ordem(), [])
        self.assertEqual(a.altura(), -1)
        self.assertEqual(a.tamanho(), 0)
        self.assertEqual(a.validar(), (True, []))

    def test_um_no(self):
        a = arvore_com(7)
        self.assertEqual(a.altura(), 0)
        self.assertEqual(a.minimo().numero, 7)
        self.assertEqual(a.maximo().numero, 7)

    def test_caminhamentos(self):
        a = arvore_com(4, 2, 6, 1, 3, 5, 7)
        self.assertEqual(chaves(a.pre_ordem()), [4, 2, 1, 3, 6, 5, 7])
        self.assertEqual(chaves(a.em_ordem()), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(chaves(a.pos_ordem()), [1, 3, 2, 5, 7, 6, 4])

    def test_minimo_maximo(self):
        a = arvore_com(50, 20, 80, 10, 90, 60)
        self.assertEqual(a.minimo().numero, 10)
        self.assertEqual(a.maximo().numero, 90)

    def test_nil_nunca_aparece(self):
        a = arvore_com(*range(1, 50))
        for c in a.pre_ordem() + a.em_ordem() + a.pos_ordem():
            self.assertIsNotNone(c)
        self.assertNotIn("None", a.exibir())

    def test_arvores_tem_sentinelas_independentes(self):
        self.assertIsNot(ArvoreRubroNegra().NIL, ArvoreRubroNegra().NIL)


class TestExibir(unittest.TestCase):
    def test_vazia(self):
        self.assertEqual(ArvoreRubroNegra().exibir(), "(árvore vazia)")

    def test_deitada_com_cores(self):
        a = arvore_com(10, 20, 30)
        self.assertEqual(a.exibir(), "    30 (V)\n20 (P)\n    10 (V)")


class TestValidador(unittest.TestCase):
    """validar() precisa detectar árvores corrompidas de propósito."""

    def _arvore(self):
        # 20P; 10P(-, 15V); 30P
        a = arvore_com(20, 10, 30, 15)
        self.assertEqual(a.validar(), (True, []))
        return a

    def _invalida(self, a, trecho):
        ok, violacoes = a.validar()
        self.assertFalse(ok)
        self.assertTrue(any(trecho in v for v in violacoes), violacoes)

    def test_raiz_vermelha(self):
        a = self._arvore()
        a._raiz.cor = VERMELHO
        self._invalida(a, "raiz 20 não é preta")

    def test_vermelho_vermelho(self):
        a = self._arvore()
        no_de(a, 10).cor = VERMELHO
        self._invalida(a, "vermelho-vermelho")

    def test_altura_negra_diferente(self):
        a = self._arvore()
        no_de(a, 15).cor = PRETO
        self._invalida(a, "altura negra diferente")

    def test_ordem_violada_em_neto(self):
        # 25 fica à direita do 10 (localmente ok), mas está na subárvore
        # esquerda do 20 → só a checagem com limites propagados pega.
        a = self._arvore()
        no_de(a, 15).conta = conta(25)
        self._invalida(a, "ordem violada em 25")

    def test_pai_inconsistente(self):
        a = self._arvore()
        no_de(a, 15).pai = no_de(a, 30)
        self._invalida(a, "pai de 15")

    def test_nil_vermelho(self):
        a = self._arvore()
        a.NIL.cor = VERMELHO
        self._invalida(a, "NIL não é preto")

    def test_tamanho_errado(self):
        a = self._arvore()
        a._tamanho = 99
        self._invalida(a, "tamanho")


class TestModoDetalhado(unittest.TestCase):
    def _detalhada(self, sequencia):
        a = ArvoreRubroNegra()
        a.definir_modo_detalhado(True)
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            for k in sequencia:
                a.inserir(conta(k))
        return a, saida.getvalue()

    def test_mesma_arvore_e_mensagens(self):
        # 10, 30, 20 → triângulo RL; 5 → tio vermelho; 1 → linha LL
        sequencia = [10, 30, 20, 5, 1]
        normal = arvore_com(*sequencia)
        detalhada, texto = self._detalhada(sequencia)

        self.assertEqual(cores(normal), cores(detalhada))
        self.assertEqual(normal.estatisticas(), detalhada.estatisticas())
        self.assertIn("[RN] ", texto)
        self.assertIn("triângulo (RL)", texto)
        self.assertIn("vermelho → recolorir", texto)
        self.assertIn("linha (LL)", texto)

    def test_formato_do_plano(self):
        _, texto = self._detalhada([25, 20, 30, 10])
        self.assertIn("[RN] inserido 10 sob 20", texto)
        self.assertIn("[RN] tio 30 vermelho → recolorir 20(P), 30(P), 25(V)", texto)

    def test_remocao_mesma_arvore_e_mensagens(self):
        insercoes = list(range(1, 32))
        remocoes = [1, 3, 2, 8, 16, 31, 24, 20, 12, 5]
        normal = arvore_com(*insercoes)
        detalhada, _ = self._detalhada(insercoes)
        normal.resetar_estatisticas()
        detalhada.resetar_estatisticas()

        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            for k in remocoes:
                detalhada.remover(k)
            detalhada.remover(999)
        for k in remocoes:
            normal.remover(k)

        self.assertEqual(cores(normal), cores(detalhada))
        self.assertEqual(normal.estatisticas(), detalhada.estatisticas())
        texto = saida.getvalue()
        self.assertIn("[RN] remover 16: 2 filhos → sucessor 17", texto)
        self.assertIn("caso 2:", texto)
        self.assertIn("remoção 999: não encontrada", texto)

    def test_desligado_nao_imprime(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            a = arvore_com(30, 20, 10, 5, 25)
            a.buscar(10)
            a.remover(20)
            a.remover(99)
        self.assertEqual(saida.getvalue(), "")

    def test_mensagens_de_cada_caso_da_remocao(self):
        estruturas = {
            "caso 1:": ((20, P, (10, P), (30, V, (25, P), (35, P))), 10),
            "caso 1 (espelho)": ((20, P, (10, V, (5, P), (15, P)), (30, P)), 30),
            "caso 3:": ((20, P, (10, P), (30, P, (25, V), None)), 10),
            "caso 3 (espelho)": ((20, P, (10, P, None, (15, V)), (30, P)), 30),
            "caso 4: sobrinho distante 35": ((20, P, (10, P), (30, P, None, (35, V))), 10),
            "caso 4: sobrinho distante 5": ((20, P, (10, P, (5, V), None), (30, P)), 30),
        }
        for trecho, (estrutura, numero) in estruturas.items():
            with self.subTest(trecho=trecho):
                a = montar(estrutura)
                a.definir_modo_detalhado(True)
                saida = io.StringIO()
                with contextlib.redirect_stdout(saida):
                    a.remover(numero)
                self.assertIn(trecho, saida.getvalue())


if __name__ == "__main__":
    unittest.main()
