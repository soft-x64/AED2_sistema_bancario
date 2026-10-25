"""Testes dos cenários A/B (I1).

A RN é injetada como uma segunda AVL ("RN_FAKE"), para os testes rodarem antes
de rubro_negra.py existir e sem depender da correção dela. O que se testa aqui
é o EXPERIMENTO: mesmas listas, sementes, ordem alternada, colunas e cronômetro.
"""

import contextlib
import io
import unittest
from unittest import mock

import experimentos_insercao as exp
import gerador
from avl import ArvoreAVL

ESTRUTURAS = [("AVL", ArvoreAVL), ("RN_FAKE", ArvoreAVL)]


class ArvoreEspiã(ArvoreAVL):
    """AVL que registra as chaves recebidas e a ordem de criação."""
    log_criacao: list[str] = []

    def __init__(self, rotulo):
        super().__init__()
        self.recebidas = []
        ArvoreEspiã.log_criacao.append(rotulo)

    def inserir(self, conta):
        self.recebidas.append(conta)
        return super().inserir(conta)


class TestCenarios(unittest.TestCase):
    def test_a_crescente(self):
        self.assertEqual(exp.chaves_do_cenario("A", 5, 3), [1, 2, 3, 4, 5])

    def test_b_permutacao_reproduzivel(self):
        b1 = exp.chaves_do_cenario("B", 1000, 2)
        self.assertEqual(b1, exp.chaves_do_cenario("B", 1000, 2))
        self.assertEqual(sorted(b1), list(range(1, 1001)))
        self.assertNotEqual(b1, list(range(1, 1001)))
        self.assertNotEqual(b1, exp.chaves_do_cenario("B", 1000, 3))  # rep muda a semente

    def test_semente_oficial(self):
        self.assertEqual(gerador.SEMENTE_BASE, 2026)
        self.assertEqual(gerador.semente_permutacao(1000, 2), 2026 + 2000 + 1000)
        # A/B usam a MESMA função do gerador que C/D usam (fonte única)
        self.assertIs(exp.semente_permutacao, gerador.semente_permutacao)

    def test_cenario_invalido(self):
        with self.assertRaises(ValueError):
            exp.chaves_do_cenario("C", 10, 0)


class TestJustica(unittest.TestCase):
    def _executar_com_espias(self, repeticao):
        ArvoreEspiã.log_criacao = []
        criadas = {}

        def fabrica(rotulo):
            def criar():
                criadas[rotulo] = ArvoreEspiã(rotulo)
                return criadas[rotulo]
            return criar

        linhas = exp.executar_cenario_insercao(
            "B", 200, repeticao, [("AVL", fabrica("AVL")), ("RN", fabrica("RN"))])
        return linhas, criadas

    def test_mesma_lista_e_mesmos_objetos(self):
        _, criadas = self._executar_com_espias(0)
        avl, rn = criadas["AVL"].recebidas, criadas["RN"].recebidas
        self.assertEqual(len(avl), 200)
        self.assertTrue(all(a is b for a, b in zip(avl, rn)))  # os MESMOS objetos Conta

    def test_ordem_alternada(self):
        self._executar_com_espias(0)
        self.assertEqual(ArvoreEspiã.log_criacao, ["AVL", "RN"])
        linhas, _ = self._executar_com_espias(1)
        self.assertEqual(ArvoreEspiã.log_criacao, ["RN", "AVL"])
        # mas a saída sempre vem na ordem fixa (AVL, RN)
        self.assertEqual([l["estrutura"] for l in linhas], ["AVL", "RN"])

    def test_cronometro_so_envolve_insercoes(self):
        # Se validar() rodasse dentro do cronômetro, perf_counter seria chamado
        # depois dele. Aqui conferimos que a validação acontece após o 2º perf_counter.
        eventos = []
        relogio_real = exp.time.perf_counter

        def relogio():
            eventos.append("tempo")
            return relogio_real()

        validar_real = ArvoreAVL.validar

        def validar(self):
            eventos.append("validar")
            return validar_real(self)

        with mock.patch.object(exp.time, "perf_counter", relogio), \
             mock.patch.object(ArvoreAVL, "validar", validar):
            exp.executar_cenario_insercao("A", 50, 0, [("AVL", ArvoreAVL)])
        self.assertEqual(eventos, ["tempo", "tempo", "validar"])

    def test_sem_saida_no_terminal(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            exp.executar_cenario_insercao("B", 300, 0, ESTRUTURAS)
        self.assertEqual(saida.getvalue(), "")


class TestLinhas(unittest.TestCase):
    def test_colunas_do_csv(self):
        linha = exp.executar_cenario_insercao("A", 100, 0, ESTRUTURAS)[0]
        self.assertEqual(tuple(exp.linha_csv(linha)), exp.COLUNAS_CSV)

    def test_valores_avl(self):
        linha = exp.executar_cenario_insercao("A", 1023, 0, ESTRUTURAS)[0]
        self.assertEqual(linha["estrutura"], "AVL")
        self.assertEqual(linha["altura_depois"], 9)      # 1..1023 crescente → perfeita
        self.assertEqual(linha["tamanho_depois"], 1023)
        self.assertEqual(linha["recoloracoes"], "nao_se_aplica")
        self.assertIs(linha["valido"], True)
        self.assertGreater(linha["tempo_s"], 0)
        self.assertEqual(linha["percentual"], "")         # sem sentido em A/B

    def test_casos_avl_a_versus_b(self):
        a = exp.executar_cenario_insercao("A", 1000, 0, ESTRUTURAS)[0]["_casos_avl"]
        b = exp.executar_cenario_insercao("B", 1000, 0, ESTRUTURAS)[0]["_casos_avl"]
        self.assertEqual((a["LL"], a["LR"], a["RL"]), (0, 0, 0))  # crescente: só RR
        self.assertTrue(all(v > 0 for v in b.values()))           # aleatório: todos

    def test_invalida_se_arvore_quebrada(self):
        class Quebrada(ArvoreAVL):
            def validar(self):
                return False, ["simulado"]
        linha = exp.executar_cenario_insercao("A", 10, 0, [("AVL", Quebrada)])[0]
        self.assertIs(linha["valido"], False)


if __name__ == "__main__":
    unittest.main()
