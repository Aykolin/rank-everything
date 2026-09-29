<div align="center">
  <img src="store-assets/feature-graphic-1024x500.png" alt="Rank Everything" width="100%">

  <h1>Rank Everything</h1>

  <p>Crie rankings pessoais sobre qualquer assunto, compare opções e descubra o seu verdadeiro favorito.</p>
</div>

## Sobre o projeto

O **Rank Everything** é um aplicativo mobile para organizar opiniões em rankings. Ele funciona offline, não exige conta e mantém os dados no próprio aparelho.

O projeto foi desenvolvido em Python com Flet, usa SQLite para persistência local e segue a identidade visual Catppuccin Mocha.

## Recursos

- criação e exclusão de rankings;
- classificação manual por posição;
- classificação automática por nota;
- inserção de itens por comparação direta;
- reorganização por arrastar e soltar;
- comandos acessíveis para mover itens para cima ou para baixo;
- busca local de rankings;
- 24 símbolos temáticos e 14 cores de capa;
- layout responsivo para celulares, tablets e desktop;
- navegação compatível com o botão e o gesto Voltar do Android;
- armazenamento local em SQLite;
- funcionamento offline, sem anúncios e sem cadastro;
- interface disponível em Português (Brasil) e English;
- ícone adaptativo para Android.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python 3.10+ | Lógica e estrutura do aplicativo |
| Flet 1.0 | Interface multiplataforma |
| SQLite | Persistência local |
| Pytest | Testes automatizados |
| Catppuccin Mocha | Paleta e identidade visual |

## Executando localmente

Clone ou baixe o repositório e entre na pasta do projeto.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install flet-cli==1.0.1 flet-web==1.0.1 pytest==8.4.2
flet run --web
```

### Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install flet-cli==1.0.1 flet-web==1.0.1 pytest==8.4.2
flet run --web
```

A versão web ficará disponível no endereço exibido pelo Flet, normalmente `http://127.0.0.1:8550`.

Para abrir como aplicativo desktop:

```bash
flet run
```

## Testes

Com o ambiente virtual ativado, execute:

```bash
pytest -q
```

Os testes cobrem regras de ordenação, comparação, persistência, migrações, navegação e perfis responsivos.

## Gerando o APK para Android

```bash
flet build apk
```

O arquivo será criado dentro da pasta `build/apk/` e pode ser instalado manualmente em um dispositivo Android para uso pessoal ou testes.

## Estrutura do projeto

```text
rank_everything/
├── assets/
├── src/
│   ├── main.py
│   ├── assets/
│   │   └── icon.png
│   └── rank_everything/
│       ├── app.py
│       ├── database.py
│       ├── i18n.py
│       ├── layout.py
│       ├── models.py
│       ├── navigation.py
│       ├── repository.py
│       ├── services.py
│       └── theme.py
├── tests/
├── pyproject.toml
└── README.md
```

## Dados e privacidade

Os rankings são armazenados no banco local `rank_everything.db`. O aplicativo não exige cadastro e não envia o conteúdo criado pelo usuário para um servidor externo.

Durante o desenvolvimento, o banco fica na pasta `data/`, que não é versionada. No Android, ele fica no armazenamento privado do aplicativo.

## Status

O projeto está em desenvolvimento e já possui uma versão funcional para uso pessoal e testes locais.

