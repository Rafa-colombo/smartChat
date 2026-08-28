import pytest
import respx
from httpx import Response, ReadTimeout

from src.tools.viacep import consultar_cep
from src.tools.pokeapi import consultar_pokemon

@respx.mock
def test_consultar_cep_sucesso():
    """Testa o retorno com sucesso da API ViaCEP."""
    cep_exemplo = "01001000"
    url_mock = f"https://viacep.com.br/ws/{cep_exemplo}/json/"
    
    respx.get(url_mock).mock(
        return_value=Response(
            200,
            json={
                "cep": "01001-000",
                "logradouro": "Praça da Sé",
                "bairro": "Sé",
                "localidade": "São Paulo",
                "uf": "SP"
            }
        )
    )
    
    resultado = consultar_cep(cep_exemplo)
    
    assert isinstance(resultado, dict)
    assert resultado["localidade"] == "São Paulo"
    assert resultado["uf"] == "SP"
    assert resultado["logradouro"] == "Praça da Sé"

def test_consultar_cep_invalido():
    """Testa a validação de um CEP com formato incorreto."""
    resultado = consultar_cep("123") # Menos de 8 dígitos
    assert isinstance(resultado, dict)
    assert "erro" in resultado

@respx.mock
def test_consultar_pokemon_sucesso():
    """Testa o retorno com sucesso da PokéAPI."""
    nome_pokemon = "pikachu"
    url_mock = f"https://pokeapi.co/api/v2/pokemon/{nome_pokemon}"
    
    respx.get(url_mock).mock(
        return_value=Response(
            200,
            json={
                "name": "pikachu",
                "id": 25,
                "height": 4,
                "weight": 60,
                "types": [{"type": {"name": "electric"}}],
                "abilities": [{"ability": {"name": "static"}}],
            }
        )
    )
    
    resultado = consultar_pokemon(nome_pokemon)
    assert isinstance(resultado, dict)
    assert resultado["nome"] == "pikachu"
    assert resultado["id"] == 25
    assert "electric" in resultado["tipos"]

