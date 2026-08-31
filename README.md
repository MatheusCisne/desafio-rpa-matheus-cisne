# Desafio Técnico de RPA — Matheus Cisne

Automação do [RPA Challenge](https://rpachallenge.com/) entregue em **duas soluções
independentes e completas**, conforme pedido no desafio: uma 100% em Python, outra 100% em
UiPath. Nenhuma das duas chama a outra.

## Estrutura do repositório

```
desafio-rpa-matheus-cisne/
├── python/         → solução 100% Python (Playwright + pandas). Ver python/README.md
├── uipath/         → solução 100% UiPath. Ver uipath/README.md
├── evidencias/      → screenshots do resultado final de cada solução + link do vídeo
├── USO_DE_IA.md     → registro de uso de IA durante o desenvolvimento
└── .gitignore
```

## Onde encontrar cada coisa

- **Solução Python**: [python/README.md](python/README.md) — problema resolvido, decisões
  técnicas (por que pandas em vez de openpyxl, por que Playwright), como instalar e executar,
  como os campos dinâmicos foram identificados, tratamento de erros/logs, dificuldades e
  limitações.
- **Solução UiPath**: [uipath/README.md](uipath/README.md) — problema resolvido, decisões
  técnicas (por que um único card de navegador, por que WebClient para o download), como
  instalar e executar, dificuldades e limitações.
- **Evidências**:
  - [evidencias/resultado-python.png](evidencias/resultado-python.png) — resultado final da
    execução em Python (100%, 70/70 campos).
  - [evidencias/resultado-uipath.png](evidencias/resultado-uipath.png) — resultado final da
    execução em UiPath (100%, 70/70 campos).
  - [evidencias/link-do-video.txt](evidencias/link-do-video.txt) — link do vídeo curto
    mostrando as duas soluções rodando.
- **Uso de IA**: [USO_DE_IA.md](USO_DE_IA.md).

## O problema

O RPA Challenge exibe um formulário de 7 campos que trocam de posição na tela a cada uma das
10 rodadas. Cada solução precisa: baixar o Excel de entrada diretamente do site, ler e validar
os dados, e preencher cada rodada localizando cada campo pelo **significado** (não pela posição
na tela), registrando início, fim e erros da execução.
