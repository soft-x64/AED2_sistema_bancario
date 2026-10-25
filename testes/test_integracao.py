"""Testes de integração: aplicação (coleção comum), menu e executor de experimentos.

Responsável: I3 · Revisor: I2
"""

import contextlib
import io
import random
import unittest
from decimal import Decimal
from unittest import mock

import experimentos
import gerador
import main
from aplicacao import AplicacaoBancaria, ContaDuplicada, InconsistenciaEntreArvores


def mesma_colecao(app) -> bool:
    """AVL e RN guardam as mesmas contas (todos os atributos), na mesma ordem."""
    return app.avl.em_ordem() == app.rn.em_ordem()


class TestColecaoComum(unittest.TestCase):
    def setUp(self):
        self.app = AplicacaoBancaria()

    def test_cadastro_vai_para_as_duas(self):
        conta = self.app.cadastrar("000123", " Maria  Silva ", "12", "corrente", "1500,5")
        self.assertEqual(conta.numero, 123)
        self.assertEqual(conta.saldo, Decimal("1500.50"))
        self.assertIs(self.app.avl.buscar(123), conta)
        self.assertIs(self.app.rn.buscar(123), conta)

    def test_remocao_sai_das_duas(self):
        self.app.cadastrar(10, "Teste Um", 1, "CORRENTE", "100")
        self.app.cadastrar(20, "Teste Dois", 2, "POUPANCA", "200")
        self.assertEqual(self.app.remover("10").numero, 10)
        self.assertIsNone(self.app.avl.buscar(10))
        self.assertIsNone(self.app.rn.buscar(10))
        self.assertEqual((self.app.avl.tamanho(), self.app.rn.tamanho()), (1, 1))

    def test_duplicata_rejeitada_sem_alterar(self):
        original = self.app.cadastrar(10, "Ana Silva", 1, "CORRENTE", "100")
        with self.assertRaises(ContaDuplicada):
            self.app.cadastrar(10, "Bruno Dias", 2, "POUPANCA", "999")
        self.assertIs(self.app.buscar(10), original)
        self.assertEqual(self.app.tamanho(), 1)
        self.assertTrue(mesma_colecao(self.app))

    def test_remover_inexistente(self):
        self.app.cadastrar(10, "Ana Silva", 1, "CORRENTE", "100")
        self.assertIsNone(self.app.remover(99))
        self.assertEqual(self.app.tamanho(), 1)

    def test_entradas_invalidas_nao_alteram_nada(self):
        invalidos = [
            ("+123", "Ana Silva", "1", "CORRENTE", "10"),
            ("1_000", "Ana Silva", "1", "CORRENTE", "10"),
            ("12", "Ana Silva", "1", "CORRENTE", "1e2"),
            ("12", "Ana Silva", "1", "CORRENTE", "-0"),
            ("12", "A", "1", "CORRENTE", "10"),
            ("12", "Ana Silva", "12345", "CORRENTE", "10"),
            ("12", "Ana Silva", "1", "SALARIO", "10"),
        ]
        for dados in invalidos:
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                self.app.cadastrar(*dados)
        self.assertEqual((self.app.avl.tamanho(), self.app.rn.tamanho()), (0, 0))
        for numero in ("+5", "abc", "0", ""):
            with self.subTest(numero=numero), self.assertRaises(ValueError):
                self.app.buscar(numero)

    def test_operacoes_aleatorias_mantem_colecao_comum(self):
        rng = random.Random(2026)
        referencia = {}
        for _ in range(1500):
            k = rng.randint(1, 300)
            if rng.random() < 0.55:
                if k in referencia:
                    with self.assertRaises(ContaDuplicada):
                        self.app.cadastrar(k, f"Titular {k}", k % 9999 + 1, "CORRENTE", "1")
                else:
                    referencia[k] = self.app.cadastrar(k, f"Titular {k}", k % 9999 + 1,
                                                       "CORRENTE", "1")
            else:
                self.assertEqual(self.app.remover(k), referencia.pop(k, None))
            self.assertTrue(mesma_colecao(self.app))
        self.assertEqual([c.numero for c in self.app.em_ordem()], sorted(referencia))
        self.assertEqual(self.app.validar(), (True, []))


class TestArvoreAtiva(unittest.TestCase):
    def setUp(self):
        self.app = AplicacaoBancaria()
        for k in (20, 10, 30):
            self.app.cadastrar(k, f"Titular {k}", 1, "CORRENTE", "1")
        self.app.resetar_estatisticas()

    def test_nomes_aceitos(self):
        for nome, esperado in (("avl", "AVL"), ("RN", "RN"), (" rubro-negra ", "RN"),
                               ("Rubro Negra", "RN")):
            self.app.definir_arvore_ativa(nome)
            self.assertEqual(self.app.arvore_ativa_nome, esperado)
        with self.assertRaises(ValueError):
            self.app.definir_arvore_ativa("B+")

    def test_consulta_usa_so_a_ativa(self):
        self.app.definir_arvore_ativa("RN")
        self.app.buscar(10)
        self.assertEqual(self.app.rn.estatisticas()["buscas"], 1)
        self.assertEqual(self.app.avl.estatisticas()["buscas"], 0)
        self.assertIn("(P)", self.app.exibir())  # exibição com cores = RN


class TestDivergencia(unittest.TestCase):
    def test_insercao_divergente(self):
        app = AplicacaoBancaria()
        with mock.patch.object(app.rn, "inserir", return_value=False):
            with self.assertRaises(InconsistenciaEntreArvores):
                app.cadastrar(10, "Ana Silva", 1, "CORRENTE", "1")

    def test_remocao_divergente(self):
        app = AplicacaoBancaria()
        app.cadastrar(10, "Ana Silva", 1, "CORRENTE", "1")
        with mock.patch.object(app.rn, "remover", return_value=None):
            with self.assertRaises(InconsistenciaEntreArvores):
                app.remover(10)

    def test_validar_detecta_colecoes_diferentes(self):
        app = AplicacaoBancaria()
        app.cadastrar(10, "Ana Silva", 1, "CORRENTE", "1")
        app.avl.inserir(gerador.gerar_contas([99], 1)[0])  # só numa árvore
        ok, erros = app.validar()
        self.assertFalse(ok)
        self.assertTrue(any("coleção comum" in e for e in erros))


class TestModoDetalhado(unittest.TestCase):
    def test_mesma_colecao_com_e_sem_detalhado(self):
        contas = gerador.gerar_contas(gerador.permutacao(200, 7), 7)
        normal, detalhado = AplicacaoBancaria(), AplicacaoBancaria()
        detalhado.definir_modo_detalhado(True)
        with contextlib.redirect_stdout(io.StringIO()):
            for app in (normal, detalhado):
                for c in contas:
                    app.cadastrar(c.numero, c.titular, c.agencia, c.tipo, c.saldo)
                for c in contas[::3]:
                    app.remover(c.numero)
        self.assertEqual(normal.avl.em_ordem(), detalhado.avl.em_ordem())
        self.assertEqual(normal.rn.em_ordem(), detalhado.rn.em_ordem())
        self.assertEqual(normal.avl.estatisticas(), detalhado.avl.estatisticas())
        self.assertEqual(normal.rn.estatisticas(), detalhado.rn.estatisticas())


class TestGerador(unittest.TestCase):
    def test_mesma_semente_mesmos_dados(self):
        s = gerador.semente_permutacao(1000, 3)
        self.assertEqual(gerador.permutacao(1000, s), gerador.permutacao(1000, s))
        self.assertEqual(gerador.gerar_contas([1, 2, 3], s), gerador.gerar_contas([1, 2, 3], s))
        self.assertEqual(gerador.buscas(1000, s), gerador.buscas(1000, s))

    def test_buscas_metade_presente(self):
        chaves = gerador.buscas(500, 1)
        self.assertEqual(sorted(chaves), list(range(1, 1001)))

    def test_subconjunto(self):
        base = gerador.permutacao(1000, 5)
        sub = gerador.subconjunto_remocao(base, 30, gerador.semente_subconjunto(1000, 1, 30))
        self.assertEqual(len(sub), 300)
        self.assertEqual(len(set(sub)), 300)
        self.assertTrue(set(sub) <= set(base))


class TestExecutor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.brutos, cls.buscas = experimentos.executar(
                tamanhos=(60,), repeticoes=2, progresso=False)

    def test_quantidade_e_validade(self):
        # por repetição: A, B, C (2 estruturas cada) + D (3 percentuais × 2) = 12
        self.assertEqual(len(self.brutos), 24)
        self.assertTrue(all(l["valido"] is True for l in self.brutos))
        self.assertEqual(len(self.buscas), 2 * 2 * 120)  # reps × estruturas × 2N

    def test_buscas_por_busca_somam_o_total(self):
        for linha in (l for l in self.brutos if l["cenario"] == "C"):
            visitas = [b["nos_visitados"] for b in self.buscas
                       if b["estrutura"] == linha["estrutura"] and b["repeticao"] == linha["repeticao"]]
            self.assertEqual(sum(visitas), linha["nos_visitados"])
            self.assertTrue(all(v >= 0 for v in visitas))
            self.assertEqual(linha["buscas"], 120)

    def test_mesmos_dados_nas_duas_arvores(self):
        for cen in ("C", "D"):
            for rep in (1, 2):
                linhas = [l for l in self.brutos if l["cenario"] == cen and l["repeticao"] == rep]
                avl = [l for l in linhas if l["estrutura"] == "AVL"]
                rn = [l for l in linhas if l["estrutura"] == "RN"]
                for a, r in zip(avl, rn):
                    self.assertEqual(a["tamanho_antes"], r["tamanho_antes"])
                    self.assertEqual(a["tamanho_depois"], r["tamanho_depois"])

    def test_colunas_padrao(self):
        for linha in self.brutos:
            self.assertEqual(tuple(linha), experimentos.COLUNAS_CSV)


class TestMenu(unittest.TestCase):
    def _rodar(self, *entradas) -> str:
        saida = io.StringIO()
        # EOFError no fim simula o terminal fechando a entrada (Ctrl+Z / Ctrl+D)
        with mock.patch("builtins.input", side_effect=[*entradas, EOFError]), \
             contextlib.redirect_stdout(saida):
            main.menu()
        return saida.getvalue()

    def test_duplicata_avisada(self):
        texto = self._rodar("2", "10", "Ana Silva", "1", "corrente", "100",
                            "2", "10", "Bruno Dias", "2", "poupanca", "50", "0")
        self.assertIn("Cadastrada nas duas árvores", texto)
        self.assertIn("Já existe uma conta com o número 10", texto)

    def test_menu_nao_contorna_validacao(self):
        texto = self._rodar("2", "+123", "Carla Lima", "3", "corrente", "10",
                            "2", "12", "Carla Lima", "3", "corrente", "1e2", "0")
        self.assertEqual(texto.count("[ERRO DE VALIDAÇÃO]"), 2)
        self.assertNotIn("Cadastrada", texto)

    def test_opcao_invalida_e_saida_por_eof(self):
        texto = self._rodar("99")  # depois do 99 a entrada acaba (EOF)
        self.assertIn("Opção inválida", texto)
        self.assertIn("Encerrando", texto)


if __name__ == "__main__":
    unittest.main()
