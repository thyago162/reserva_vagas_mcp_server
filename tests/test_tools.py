import httpx
import server
import pytest

@pytest.fixture(autouse=True)
def ambiente(monkeypatch):
    monkeypatch.setenv("BACKEND_API", "http://api.teste/")
    monkeypatch.setenv("MCP_EMAIL", "mcp@teste.com")
    monkeypatch.setenv("MCP_PWD", "segredo")
    monkeypatch.setattr(server, "_token_cache", None)

class RespostaFalsa:
    def __init__(self, status_code=200, corpo=None):
        self.status_code = status_code
        self._corpo = corpo or {}

    def json(self):
        return self._corpo

def test_verificar_reserva_existe_envia_cpf_limpo(monkeypatch):
    monkeypatch.setenv("BACKEND_API", "http://api.teste/")
    urls = []

    def get_falso(url, **kwargs):
        urls.append(url)
        return RespostaFalsa(200, {"possui_reserva": False})

    monkeypatch.setattr(httpx, "get", get_falso)

    resultado = server.verificar_reserva_existe("529.982.247-25")

    assert urls == ["http://api.teste/candidato/candidato-possui-reserva/52998224725"]
    assert resultado == {"possui_reserva": False}

def test_verificar_reserva_existe_cpf_invalido_nao_chama_api(monkeypatch):
    chamadas = []
    monkeypatch.setattr(httpx, "get", lambda *a, **k: chamadas.append(1))

    resultado = server.verificar_reserva_existe("111.111.111-11")

    assert resultado["erro"] is True
    assert chamadas == []

def test_listar_escolas(monkeypatch):
   monkeypatch.setattr(httpx, "post",
                       lambda *a, **k: RespostaFalsa(200, {"access_token": "tok"}))
   capturado = {}

   def get_falso(url, **kwargs):
       capturado.update(url=url, headers=kwargs["headers"], params=kwargs["params"])
       return RespostaFalsa(200, [{"nome": "Escola A", "VagasEscolares": []}])

   monkeypatch.setattr(httpx, "get", get_falso)

   resultado = server.listar_escolas("05/05/2015", -7.1664002, -34.8428213)

   assert resultado == [{"nome": "Escola A", "VagasEscolares": []}]
   assert capturado["url"] == "http://api.teste/escolas/get-escolas-dt-nascimento"
   assert capturado["headers"] == {"Authorization": "Bearer tok"}
   assert capturado["params"]["data_nascimento"] == "05-05-2015"   # "/" virou "-"

def test_listar_escolas_backend_com_erro(monkeypatch):
    monkeypatch.setattr(httpx, "post",
                        lambda *a, **k: RespostaFalsa(200, {"access_token": "ok"}))
    monkeypatch.setattr(httpx, "get", lambda *a, **k: RespostaFalsa(500))

    resultado = server.listar_escolas("05/05/2015", -7.1664002, -34.8428213)

    assert resultado["erro"] is True

def test_listar_escolas_renova_token_expirado(monkeypatch):
    tokens = iter(["tok1", "tok2"])
    logins = []
    usados = []

    def post_falso(url, **kwargs):
        logins.append(url)
        return RespostaFalsa(200, {"access_token": next(tokens)})

    def get_falso(url, **kwargs):
        auth = kwargs["headers"]["Authorization"]
        usados.append(auth)
        if auth == "Bearer tok1":
            return RespostaFalsa(401)          # token vencido
        return RespostaFalsa(200, [{"nome": "Escola A"}])

    monkeypatch.setattr(httpx, "post", post_falso)
    monkeypatch.setattr(httpx, "get", get_falso)

    resultado = server.listar_escolas("05/05/2015", "-7.1", "-34.8")

    assert resultado == [{"nome": "Escola A"}]
    assert len(logins) == 2                          # logou duas vezes
    assert usados == ["Bearer tok1", "Bearer tok2"]  # retentou com o token novo
    assert server._token_cache == "tok2"             # cache ficou co