import httpx
import server

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