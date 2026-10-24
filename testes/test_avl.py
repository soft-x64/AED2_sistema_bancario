"""Testes da AVL — Etapa 1 (busca, inserção, rotações, consultas, estatísticas)."""

import contextlib
import io
import random
import unittest

from avl import ArvoreAVL
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