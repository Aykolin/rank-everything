# Checklist de publicação na Google Play

## Já preparado no projeto

- Identificador fixo: `com.rankeverything.rank_everything`.
- Versão pública `0.5.0` e código interno `5`.
- Android 16 / API 36 como alvo.
- AAB configurado como formato de publicação.
- Ícone adaptativo do aplicativo.
- Ícone de alta resolução 512 × 512.
- Imagem de destaque 1024 × 500.
- Descrições em português do Brasil.
- Política de privacidade em português.
- Declaração inicial de segurança de dados.
- Tráfego HTTP sem criptografia desativado.
- Backup automático do banco local desativado.
- Navegação compatível com o botão e gesto Voltar do Android.

## Necessário antes de enviar

1. Criar ou validar a conta de desenvolvedor no Google Play Console.
2. Definir um e-mail público de suporte e substituir `SEU_EMAIL_DE_SUPORTE` nos documentos.
3. Hospedar a política de privacidade em uma URL pública HTTPS.
4. Criar e guardar com segurança a chave de upload `.jks`.
5. Gerar o AAB assinado executando `tools/build-playstore.ps1`.
6. Capturar pelo menos duas imagens reais do aplicativo em um celular.
7. Criar o aplicativo no Play Console usando exatamente o identificador do pacote.
8. Ativar o Play App Signing.
9. Preencher “Segurança dos dados”, “Acesso ao app”, “Anúncios”, público-alvo e classificação de conteúdo.
10. Enviar primeiro para o teste interno e validar instalação, atualização, rotação e botão Voltar.
11. Só depois promover para produção.

## Proteção da chave

Nunca envie o arquivo `.jks` ou as senhas para o repositório. Faça pelo menos duas cópias protegidas da chave de upload e mantenha as senhas em um gerenciador de senhas.
