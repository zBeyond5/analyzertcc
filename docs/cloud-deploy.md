# Publicação privada no Streamlit Community Cloud

Repositório pretendido: `zBeyond5/analyzertcc`, privado.
Endereço pretendido: `https://analyzertcc.streamlit.app`, sujeito à disponibilidade no painel.

Configuração de publicação:

- Branch: `main`.
- Arquivo principal: `cloud/app.py`.
- Python: `3.12`, selecionado nas configurações avançadas.
- Dependências: `requirements.txt` na raiz, que inclui `requirements.lock`.
- Privacidade: aplicativo privado; conferir explicitamente em Share/Settings antes de enviar dados.

O arquivo `cloud/.streamlit/config.toml` é específico da entrada da nuvem. O `app.py` e os scripts Windows/Hamachi continuam usando a configuração local. O bloqueio exclusivo de diretório usa a API nativa de cada sistema (msvcrt no Windows, flock no Linux).

O código pode ser publicado; `fontes/`, `fixtures/source/`, `.venv/`, `runtime/`, uploads, resultados e segredos não são versionados. A base incluída nos testes é explicitamente fictícia. Cada instalação tem sessões e resultados próprios, sem sincronização entre Windows e nuvem.

O disco e as sessões da nuvem são temporários. Reinício ou hibernação podem exigir nova importação. Dados reais são enviados e processados no servidor remoto e exigem as confirmações científicas/éticas apropriadas. A confirmação do algoritmo PSQI permanece pendente; publicar não equivale a validar esse instrumento.
