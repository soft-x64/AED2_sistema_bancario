"""Testes da AVL — Etapas 1, 2 e 3 (inserção, busca, remoção, validação, exibição)."""

import contextlib
import io
import random
import unittest
from decimal import Decimal

from avl import ArvoreAVL, _NoAVL
from auxiliares import chaves, conta, verificar_avl


def arvore_com(*numeros: int) -> ArvoreAVL:
    a = ArvoreAVL()
    for n in numeros:
        a.inserir(conta(n))
    return a


class TestRotacoes(unittest.TestCase):
    """Os quatro casos clássicos, com os contadores do PLANO.md (seção 8)."""

    def _conferir(self, sequencia, rotacoes_esperadas):
        a = arvore_com(*sequencia)
        self.assertEqual(chaves(a.pre_ordem()), [20, 10, 30])
        self.assertEqual(a.estatisticas()["rotacoes"], rotacoes_esperadas)
        self.assertEqual(a.altura(), 1)
        verificar_avl(a)

    def test_ll(self):
        self._conferir([30, 20, 10], 1)

    def test_rr(self):
        self._conferir([10, 20, 30], 1)

    def test_lr(self):
        self._conferir([30, 10, 20], 2)

    def test_rl(self):
        self._conferir([10, 30, 20], 2)

    def test_sem_rotacao(self):
        a = arvore_com(20, 10, 30)
        self.assertEqual(a.estatisticas()["rotacoes"], 0)

    def test_rotacao_em_no_interno(self):
        # 10 desbalanceia o 30 (não a raiz) → caso LL só naquela subárvore
        a = arvore_com(50, 30, 70, 20, 60, 80, 10)
        verificar_avl(a)
        self.assertEqual(a.estatisticas()["rotacoes"], 1)
        self.assertEqual(chaves(a.pre_ordem()), [50, 20, 10, 30, 70, 60, 80])


class TestInsercao(unittest.TestCase):
    def test_duplicata_rejeitada_sem_sobrescrever(self):
        a = ArvoreAVL()
        original = conta(10, titular="Ana")
        self.assertTrue(a.inserir(original))
        self.assertFalse(a.inserir(conta(10, titular="Bruno")))
        self.assertEqual(a.tamanho(), 1)
        self.assertIs(a.buscar(10), original)

    def test_duplicata_profunda_nao_rotaciona(self):
        a = arvore_com(20, 10, 30, 5)
        antes = a.estatisticas()["rotacoes"]
        self.assertFalse(a.inserir(conta(5)))
        self.assertEqual(a.estatisticas()["rotacoes"], antes)
        self.assertEqual(a.tamanho(), 4)
        verificar_avl(a)

    def test_crescente_gera_arvore_perfeita(self):
        # 1..1023 em ordem crescente produz uma árvore perfeita de altura 9
        a = arvore_com(*range(1, 1024))
        self.assertEqual(verificar_avl(a), (9, 1023))

    def test_aleatorio_contra_referencia(self):
        rng = random.Random(2026)
        a, referencia = ArvoreAVL(), set()
        for i in range(2000):
            k = rng.randint(1, 3000)
            self.assertEqual(a.inserir(conta(k)), k not in referencia)
            referencia.add(k)
            if i % 100 == 0:
                verificar_avl(a)
        verificar_avl(a)
        self.assertEqual(chaves(a.em_ordem()), sorted(referencia))

    def test_insercao_nao_conta_nos_visitados(self):
        a = arvore_com(5, 3, 8, 1)
        self.assertEqual(a.estatisticas()["nos_visitados"], 0)


class TestBusca(unittest.TestCase):
    def test_contagem_de_visitas(self):
        a = arvore_com(20, 10, 30)
        self.assertEqual(a.buscar(10).numero, 10)   # visita 20, 10
        self.assertIsNone(a.buscar(25))             # visita 20, 30
        e = a.estatisticas()
        self.assertEqual(e["nos_visitados"], 4)
        self.assertEqual(e["buscas"], 2)

    def test_resetar_estatisticas(self):
        a = arvore_com(30, 20, 10)
        a.buscar(10)
        a.resetar_estatisticas()
        self.assertEqual(
            a.estatisticas(),
            {"rotacoes": 0, "recoloracoes": None, "nos_visitados": 0, "buscas": 0},
        )
        self.assertEqual(a.tamanho(), 3)  # reset não mexe na árvore


class TestConsultas(unittest.TestCase):
    def test_arvore_vazia(self):
        a = ArvoreAVL()
        self.assertIsNone(a.buscar(1))
        self.assertIsNone(a.minimo())
        self.assertIsNone(a.maximo())
        self.assertEqual(a.pre_ordem(), [])
        self.assertEqual(a.em_ordem(), [])
        self.assertEqual(a.pos_ordem(), [])
        self.assertEqual(a.altura(), -1)
        self.assertEqual(a.tamanho(), 0)

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


class TestRemocao(unittest.TestCase):
    """Etapa 2 — remoção com rebalanceamento."""

    # Árvore de Fibonacci de altura 4: a AVL mais "magra" possível com 12 nós.
    # Qualquer remoção do lado raso pode desbalancear vários níveis.
    FIBONACCI = (8, 5, 11, 3, 7, 10, 12, 2, 4, 6, 9, 1)

    def test_caso_do_plano(self):
        # 4,2,6,1,3 → remover 6: o 4 fica com FB=+2 e o 2 tem FB=0 → LL
        a = arvore_com(4, 2, 6, 1, 3)
        a.resetar_estatisticas()
        self.assertEqual(a.remover(6).numero, 6)
        self.assertEqual(chaves(a.pre_ordem()), [2, 1, 4, 3])
        self.assertEqual(a.estatisticas()["rotacoes"], 1)
        verificar_avl(a)

    def test_rebalanceamento_em_varios_niveis(self):
        a = arvore_com(*self.FIBONACCI)
        self.assertEqual(a.altura(), 4)
        a.resetar_estatisticas()
        a.definir_modo_detalhado(True)
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            a.remover(12)
        # rebalanceia primeiro em 11, depois na raiz 8 (dois níveis diferentes)
        self.assertEqual(saida.getvalue().count("desbalanceado"), 2)
        self.assertIn("desbalanceado em 11", saida.getvalue())
        self.assertIn("desbalanceado em 8", saida.getvalue())
        self.assertEqual(a.estatisticas()["rotacoes"], 2)
        self.assertEqual(chaves(a.pre_ordem()), [5, 3, 2, 1, 4, 8, 7, 6, 10, 9, 11])
        verificar_avl(a)

    def test_folha(self):
        a = arvore_com(20, 10, 30)
        a.remover(10)
        self.assertEqual(chaves(a.pre_ordem()), [20, 30])
        verificar_avl(a)

    def test_um_filho(self):
        a = arvore_com(20, 10, 30, 35)
        a.remover(30)  # 30 só tem o filho direito 35
        self.assertEqual(chaves(a.pre_ordem()), [20, 10, 35])
        verificar_avl(a)

    def test_dois_filhos_preserva_atributos(self):
        a = ArvoreAVL()
        for k in (20, 10, 30, 25, 40):
            a.inserir(conta(k, titular=f"Titular {k}", saldo=Decimal(k)))
        removida = a.remover(20)  # raiz com 2 filhos; sucessor = 25
        # retorna a conta ORIGINAL do 20, não a do sucessor
        self.assertEqual(removida.numero, 20)
        self.assertEqual(removida.titular, "Titular 20")
        # o sucessor subiu com TODOS os seus atributos
        novo = a.buscar(25)
        self.assertEqual(novo.titular, "Titular 25")
        self.assertEqual(novo.saldo, Decimal(25))
        self.assertEqual(chaves(a.pre_ordem()), [25, 10, 30, 40])
        self.assertIsNone(a.buscar(20))
        verificar_avl(a)

    def test_dois_filhos_sucessor_profundo(self):
        # sucessor de 50 é 55, que está no fundo da subárvore direita
        a = arvore_com(50, 30, 70, 20, 40, 60, 80, 55)
        self.assertEqual(a.remover(50).numero, 50)
        self.assertEqual(a.pre_ordem()[0].numero, 55)
        verificar_avl(a)

    def test_remover_raiz_unica_e_ultimo(self):
        a = arvore_com(7)
        self.assertEqual(a.remover(7).numero, 7)
        self.assertEqual((a.altura(), a.tamanho()), (-1, 0))
        self.assertIsNone(a.minimo())
        self.assertIsNone(a.remover(7))  # remover de árvore vazia
        self.assertTrue(a.inserir(conta(7)))  # árvore volta a funcionar

    def test_inexistente_nao_altera(self):
        a = arvore_com(*self.FIBONACCI)
        antes = chaves(a.pre_ordem())
        a.resetar_estatisticas()
        self.assertIsNone(a.remover(99))
        self.assertIsNone(a.remover(0))
        self.assertEqual(chaves(a.pre_ordem()), antes)
        self.assertEqual(a.tamanho(), 12)
        self.assertEqual(a.estatisticas()["rotacoes"], 0)

    def test_remocao_nao_conta_nos_visitados(self):
        a = arvore_com(5, 3, 8)
        a.remover(3)
        self.assertEqual(a.estatisticas()["nos_visitados"], 0)

    def test_esvaziar_crescente_e_aleatorio(self):
        a = arvore_com(*range(1, 201))
        for k in range(1, 201):
            a.remover(k)
            verificar_avl(a)
        self.assertEqual(a.tamanho(), 0)

        rng = random.Random(7)
        ordem = list(range(1, 201))
        rng.shuffle(ordem)
        a = arvore_com(*ordem)
        rng.shuffle(ordem)
        for k in ordem:
            self.assertEqual(a.remover(k).numero, k)
            verificar_avl(a)
        self.assertEqual(a.altura(), -1)

    def test_operacoes_aleatorias_contra_dict(self):
        """2.000 operações mistas, validando a cada passo (seção 9 do plano)."""
        rng = random.Random(2026)
        a, ref = ArvoreAVL(), {}
        for _ in range(2000):
            k = rng.randint(1, 300)
            op = rng.random()
            if op < 0.45:
                c = conta(k, titular=f"T{k}")
                self.assertEqual(a.inserir(c), k not in ref)
                ref.setdefault(k, c)
            elif op < 0.85:
                esperado = ref.pop(k, None)
                self.assertIs(a.remover(k), esperado)
            else:
                self.assertIs(a.buscar(k), ref.get(k))
            verificar_avl(a)
        self.assertEqual(chaves(a.em_ordem()), sorted(ref))


def no(numero: int, esquerda=None, direita=None, altura=None) -> _NoAVL:
    """Monta um nó à mão. Sem `altura`, calcula a correta a partir dos filhos."""
    n = _NoAVL(conta(numero))
    n.esquerda, n.direita = esquerda, direita
    if altura is None:
        h = lambda x: x.altura if x is not None else -1
        altura = 1 + max(h(esquerda), h(direita))
    n.altura = altura
    return n


def arvore_manual(raiz, tamanho: int) -> ArvoreAVL:
    """Árvore com estrutura forçada — permite criar AVLs inválidas para o validador."""
    a = ArvoreAVL()
    a._raiz, a._tamanho = raiz, tamanho
    return a


class TestValidar(unittest.TestCase):
    """Etapa 3 — o validador aceita AVLs válidas e detecta cada tipo de corrupção."""

    def test_arvores_validas(self):
        self.assertEqual(ArvoreAVL().validar(), (True, []))
        self.assertEqual(arvore_com(*TestRemocao.FIBONACCI).validar(), (True, []))
        self.assertEqual(arvore_com(*range(1, 500)).validar(), (True, []))

    def test_valida_apos_operacoes_aleatorias(self):
        rng = random.Random(99)
        a = ArvoreAVL()
        for _ in range(1000):
            k = rng.randint(1, 200)
            a.inserir(conta(k)) if rng.random() < 0.6 else a.remover(k)
            ok, erros = a.validar()
            self.assertTrue(ok, erros)

    def test_ordem_violada_so_no_neto(self):
        #     20          o 25 é maior que o pai 10 (localmente OK),
        #    /  \         mas está à ESQUERDA do 20 → deveria ser < 20.
        #  10    30       Um validador que só compara pai × filho não pega.
        #    \
        #     25
        a = arvore_manual(no(20, no(10, None, no(25)), no(30)), 4)
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertEqual(len(erros), 1)
        self.assertIn("ordem violada: 25", erros[0])

    def test_chave_igual_ao_ancestral(self):
        a = arvore_manual(no(20, no(10, None, no(20)), no(30)), 4)
        self.assertFalse(a.validar()[0])

    def test_desbalanceada(self):
        # 30 → 20 → 10 em linha: alturas corretas, mas FB=+2 na raiz
        a = arvore_manual(no(30, no(20, no(10))), 3)
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertEqual(erros, ["desbalanceado: nó 30 com FB=+2"])

    def test_altura_armazenada_errada(self):
        # estrutura balanceada, mas a raiz guarda h=5 em vez de 1
        a = arvore_manual(no(20, no(10), no(30), altura=5), 3)
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertEqual(erros, ["altura inconsistente: nó 20 guarda h=5, real h=1"])

    def test_fb_calculado_pela_altura_real(self):
        # Alturas armazenadas "maquiadas" para esconder o desbalanceamento:
        # o validador precisa recalcular, não confiar no campo altura.
        a = arvore_manual(no(30, no(20, no(10), altura=0), altura=1), 3)
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertTrue(any("FB=+2" in e for e in erros), erros)

    def test_tamanho_errado(self):
        a = arvore_com(20, 10, 30)
        a._tamanho = 7
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertEqual(erros, ["tamanho armazenado 7 ≠ número real de nós 3"])

    def test_lista_todas_as_violacoes(self):
        # ordem violada + altura errada + tamanho errado ao mesmo tempo
        a = arvore_manual(no(20, no(10, None, no(25)), no(30), altura=9), 10)
        ok, erros = a.validar()
        self.assertFalse(ok)
        self.assertEqual(len(erros), 3, erros)

    def test_validar_nao_altera_estatisticas(self):
        a = arvore_com(30, 20, 10)
        antes = a.estatisticas()
        a.validar()
        self.assertEqual(a.estatisticas(), antes)


class TestExibir(unittest.TestCase):
    def test_vazia(self):
        self.assertEqual(ArvoreAVL().exibir(), "(árvore vazia)")

    def test_um_no(self):
        self.assertEqual(arvore_com(5).exibir(), "5 [h=0, FB=0]")

    def test_formato_completo(self):
        a = arvore_com(20, 10, 30, 40)
        esperado = "\n".join([
            "    ┌── 40 [h=0, FB=0]",
            "┌── 30 [h=1, FB=-1]",
            "20 [h=2, FB=-1]",
            "└── 10 [h=0, FB=0]",
        ])
        self.assertEqual(a.exibir(), esperado)

    def test_barras_ligam_ao_pai(self):
        a = arvore_com(*TestRemocao.FIBONACCI)
        linhas = a.exibir().split("\n")
        self.assertEqual(len(linhas), 12)
        self.assertIn("│   └── 10 [h=1, FB=+1]", linhas)
        self.assertIn("8 [h=4, FB=+1]", linhas)

    def test_exibir_retorna_sem_imprimir(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            texto = arvore_com(1, 2, 3).exibir()
        self.assertEqual(saida.getvalue(), "")
        self.assertIn("2 [h=1, FB=0]", texto)


class TestModoDetalhado(unittest.TestCase):
    def test_mesma_arvore_e_mensagens(self):
        sequencia = [30, 10, 20, 40, 50]
        normal = arvore_com(*sequencia)

        detalhada = ArvoreAVL()
        detalhada.definir_modo_detalhado(True)
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            for k in sequencia:
                detalhada.inserir(conta(k))

        self.assertEqual(chaves(normal.pre_ordem()), chaves(detalhada.pre_ordem()))
        self.assertEqual(normal.estatisticas(), detalhada.estatisticas())
        texto = saida.getvalue()
        self.assertIn("caso LR", texto)
        self.assertIn("caso RR", texto)

    def test_desligado_nao_imprime(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            arvore_com(30, 20, 10).buscar(10)
        self.assertEqual(saida.getvalue(), "")


if __name__ == "__main__":
    unittest.main()