# RPA Challenge — Solução Python

Automação 100% em Python (Playwright + pandas) do [RPA Challenge](https://rpachallenge.com/):
baixa o Excel do próprio site, preenche as 10 rodadas do formulário e captura o resultado final.
Não depende da solução em UiPath.

## Problema resolvido

O RPA Challenge exibe um formulário de 7 campos que trocam de posição na tela a cada uma das
10 rodadas. A automação precisa: baixar o Excel de entrada, ler e validar os dados, e preencher
cada rodada localizando cada campo pelo **significado**, nunca pela posição/coordenada.

## Como os campos dinâmicos foram identificados

O site roda em **Angular 7 em modo desenvolvimento**, o que expõe o atributo `ng-reflect-name`
em cada `<input>` com o nome interno do campo (ex.: `labelFirstName`). Esse valor não muda entre
rodadas, mesmo com o layout embaralhando a ordem e o número de colunas — confirmado ao vivo no
navegador antes de implementar. Por isso o seletor usado é sempre:

```
input[ng-reflect-name="labelFirstName"]
```

e nunca uma coordenada de tela ou índice de posição.

**Limitação conhecida:** essa estratégia depende do site continuar em modo desenvolvimento do
Angular. Se um dia o site passar a rodar em modo produção, os atributos `ng-reflect-*` somem, e
seria necessário localizar os campos pelo texto do `<label>` (ex.: XPath
`//label[normalize-space()='First Name']/following-sibling::input`).

## Programas e versões utilizados

- Python 3.12+ (testado com Python 3.13.14)
- [Playwright](https://playwright.dev/python/) 1.62.0 para automação do navegador (Chromium, instalado via `playwright install chromium`)
- [pandas](https://pandas.pydata.org/) 3.0.5 com engine `openpyxl` 3.1.5 para ler o `.xlsx`
- `numpy` 2.5.2 (dependência transitiva do pandas)

As versões exatas de todas as dependências (diretas e transitivas) estão travadas em
`requirements.txt`.

## Decisões técnicas

O desafio permite escolher a biblioteca de automação de navegador e, no caso da leitura do
Excel, permite usar `openpyxl` puro em vez de pandas — desde que a escolha seja justificada.
As duas decisões abaixo são explicadas em cima do que o código realmente faz, não de forma
genérica.

### Pandas vs. openpyxl direto

O `openpyxl` puro resolveria a leitura do `challenge.xlsx` sem problema — o arquivo tem 7
colunas e ~10 linhas de dados, um volume trivial. A escolha por pandas (com `openpyxl` como
engine por baixo, não como substituto) foi por ergonomia de código em cima de operações que o
arquivo realmente exige, todas visíveis em `src/excel_reader.py`:

- **Seleção de colunas por nome, não por índice.** `df = df[EXPECTED_COLUMNS].dropna(how="all")`
  (linha 36) faz duas coisas em uma linha: descarta a 8ª coluna fantasma do Excel (reordenando
  e filtrando pelas 7 colunas esperadas, por nome) e mantém apenas essas colunas na ordem
  definida em `constants.py`. Com `openpyxl` puro seria preciso primeiro varrer a linha de
  cabeçalho para descobrir em qual letra/índice de coluna cada campo está (o arquivo não garante
  que "First Name" é sempre a coluna A), guardar esse mapeamento nome→índice, e só então iterar
  `sheet.iter_rows()` referenciando esse índice.
- **Descarte das linhas fantasma com uma chamada.** O Excel do desafio declara ~999 linhas no
  metadado (`sheet.dimensions` do openpyxl refletiria isso), mas só ~10 têm dado real. Em pandas,
  `dropna(how="all")` (mesma linha 36) remove de uma vez todas as linhas totalmente vazias. Com
  openpyxl puro seria necessário iterar até a linha ~999 e, para cada uma, checar manualmente se
  todas as células estão `None` antes de descartá-la.
- **Normalização de cabeçalho vetorizada.** `df.columns = [str(column).strip() for column in
  df.columns]` (linha 28) resolve o `"Last Name "` com espaço no fim de uma vez para todas as
  colunas. Essa operação específica não é mais simples em pandas do que em openpyxl — em ambos
  os casos é um `.strip()` sobre os valores da linha de cabeçalho — mas fica no mesmo lugar e no
  mesmo estilo das outras transformações acima, o que mantém a função inteira legível como uma
  sequência de passos sobre um objeto só (o DataFrame), em vez de alternar entre "acessar célula"
  e "montar dicionário manualmente".
- **Conversão de tipo em uma coluna.** `df["Phone Number"] = df["Phone Number"].apply(_normalize_phone)`
  (linha 37) aplica a normalização (`float` → `int` → `str`, evitando o sufixo `.0`) só na coluna
  de telefone, sem tocar nas demais. Com openpyxl seria o mesmo tipo de transformação, célula a
  célula, dentro do laço de iteração das linhas.
- **Formato de saída pronto para o resto do fluxo.** `df.to_dict(orient="records")` (linha 39)
  devolve exatamente a lista de dicts que `main.py` itera e que `browser_automation.fill_round`
  consome via `row.get(column, "")`. Com openpyxl, montar essa mesma lista de dicts exigiria
  construir cada `dict` manualmente dentro do laço de linhas.

**Trade-off, honestamente:** pandas (e sua dependência transitiva `numpy`) é uma biblioteca bem
mais pesada do que `openpyxl` sozinho para ler um arquivo de 7 colunas e 10 linhas — o ganho de
performance de um DataFrame não importa nesse volume de dados. A escolha foi puramente por
legibilidade: expressar "seleciona estas colunas, descarta linhas vazias, ajusta um tipo" como
uma sequência curta de operações declarativas sobre `df`, em vez de um laço manual célula a
célula. Para uma tarefa deste tamanho, `openpyxl` puro seria uma escolha igualmente válida e, em
termos de dependências, mais enxuta — é uma decisão de estilo, não uma necessidade técnica.

### Playwright vs. Selenium

O desafio permite qualquer ferramenta de automação de navegador. Playwright foi escolhido em
vez de Selenium por reduzir código boilerplate exatamente nos pontos que este script precisa,
todos visíveis em `src/browser_automation.py`:

- **Download sem gerenciar diretório do navegador.** `download_challenge_excel` usa
  `with page.expect_download() as download_info: ...` (linhas 34-37) para capturar o evento de
  download do clique em "Download Excel" e depois `download.save_as(str(dest_path))` para salvar
  onde o script quiser. Em Selenium isso exigiria configurar `prefs` no `ChromeOptions` com um
  diretório de download fixo e depois ficar checando o sistema de arquivos (polling) até o
  arquivo aparecer e parar de crescer.
- **Auto-waiting embutido, sem espera explícita.** `fill_field` (linha 57) faz
  `page.locator(selector).fill(str(value))` direto: o `locator` do Playwright espera
  automaticamente o elemento existir, estar visível e estar habilitado antes de agir. Em
  Selenium, o equivalente seguro seria envolver cada preenchimento em
  `WebDriverWait(driver, N).until(EC.element_to_be_clickable(...))` explicitamente.
- **Seletores por papel semântico (`get_by_role`).** O link de download e o botão Start são
  localizados por `page.get_by_role("link", name=DOWNLOAD_LINK_NAME)` e
  `page.get_by_role("button", name=START_BUTTON_NAME)` (linhas 35 e 45), que buscam pelo papel
  de acessibilidade e pelo texto visível do elemento — mais resistente a mudanças de classe CSS
  ou id do que um seletor `driver.find_element(By.CSS_SELECTOR, ...)` amarrado à estrutura atual
  do HTML.
- **Binário do navegador gerenciado pela própria ferramenta.** `playwright install chromium`
  (ver seção Instalação) baixa e versiona o Chromium compatível com a versão do Playwright
  instalada. Em Selenium seria necessário instalar/atualizar o ChromeDriver separadamente e
  manter sua versão sincronizada com a versão do Chrome instalado na máquina.

Selenium é mais antigo, tem comunidade maior e também resolveria o desafio — a escolha aqui foi
pela API mais moderna do Playwright reduzir a quantidade de código de espera/configuração
necessária para este fluxo específico (download + preenchimento sequencial de formulário).

## Instalação

```bash
cd python
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
playwright install chromium
```

## Como executar

```bash
python main.py
```

Não é necessário baixar o Excel manualmente nem informar caminho algum: o script abre o
site, clica em "Download Excel" e salva o arquivo automaticamente em `python/data/challenge.xlsx`
(caminho relativo ao projeto, criado na hora se não existir).

Por padrão o navegador abre visível (`headless=False`), que é o modo recomendado para uso
normal. Para rodar sem interface gráfica (por exemplo, em uma máquina/CI sem display), defina
a variável de ambiente `RPA_HEADLESS=1` antes de executar:

```bash
# PowerShell
$env:RPA_HEADLESS = "1"; python main.py

# bash
RPA_HEADLESS=1 python main.py
```

Sem essa variável definida, o comportamento é sempre "headed" (navegador visível).

### Se o navegador não abrir em modo visível (`chrome.exe`, `spawn UNKNOWN`)

Em pelo menos uma instalação do Windows testada, o Chromium isolado que o `playwright install`
baixa não conseguiu ser ativado pelo sistema operacional em modo visível, mesmo com a instalação
e os testes automatizados funcionando perfeitamente em modo headless. Vale documentar a
investigação completa aqui, porque a causa raiz é do sistema operacional, não do projeto — e a
metodologia usada para isolá-la é o que importa.

**O erro observado:**

```
playwright._impl._errors.Error: BrowserType.launch: spawn UNKNOWN
```

Esse erro do Playwright é genérico (só diz "o processo não nasceu"). Rodando o `chrome.exe`
diretamente, fora do Playwright, o Windows devolveu um erro bem mais específico:

```
Falha na inicialização do aplicativo devido à configuração lado a lado incorreta.
```

E o Log de Eventos do Windows (Visualizador de Eventos → Aplicativo → provedor `SideBySide`,
evento ID 33) detalhou ainda mais:

```
Falha na geração de contexto de ativação para "...\chrome.exe". Assembly dependente
151.0.7922.34,language="*",type="win32",version="151.0.7922.34" não pôde ser localizado.
```

**O que isso significa:** o `chrome.exe` que o Playwright baixa é um binário portátil e **não
assinado digitalmente**, que declara uma dependência interna (`chrome_elf.dll`) através de um
manifesto XML privado (`151.0.7922.34.manifest`, presente na mesma pasta), resolvido pelo
subsistema **WinSxS (Side-by-Side)** do Windows — o mesmo mecanismo usado para versionar
runtimes C++ coexistindo no sistema. Nessa máquina, essa resolução de manifesto privado falhava,
mesmo com o `chrome_elf.dll` existindo, íntegro (hash SHA-256 calculado com sucesso) e legível
no disco.

**Hipóteses descartadas, cada uma com teste e evidência (não só suposição):**

| # | Hipótese | Como foi testada | Resultado |
|---|----------|-------------------|-----------|
| 1 | Falta o Microsoft Visual C++ Redistributable (x64) | Consulta ao registro do Windows (`HKLM\...\VC\Runtimes\X64`) | Já instalado, em versão **mais nova** que a que o instalador oficial tentava aplicar (erro `0x80070666`, "outra versão já instalada") |
| 2 | Antivírus de terceiros bloqueando a execução | Checagem de processos/serviços de segurança ativos | Só o Windows Defender rodando (`MsMpEng`/`NisSrv`), nenhum AV de terceiros |
| 3 | Windows Defender bloqueando silenciosamente | `Add-MpPreference -ExclusionPath` para a pasta do Playwright, como Administrador | Exclusão aplicada; log de eventos gerou um novo erro idêntico logo depois — sem efeito |
| 4 | Arquivos de sistema do Windows corrompidos | `sfc /scannow` (como Administrador) | Encontrou e reparou arquivos corrompidos — mas o mesmo erro se repetiu, com um novo evento no log, mesmo após reiniciar o computador |
| 5 | Download do Chromium corrompido/incompleto | Apagar a pasta `chromium-1234` inteira e rodar `playwright install chromium` do zero | Download 100% novo, mesmo binário (versão `151.0.7922.34`), mesmo erro exato |

Cada uma dessas cinco é uma causa **muito mais comum** para esse tipo de erro do que a real —
por isso a ordem de investigação seguiu da mais provável para a mais rara, descartando com teste
em vez de pular direto para uma solução.

**A prova que isolou a causa:** ao pedir ao Playwright para abrir o **Microsoft Edge**
(`channel="msedge"`) em vez do Chromium isolado, funcionou de primeira — headed, 10/10 rodadas,
100%. O Edge também é Chromium por baixo dos panos, mas é instalado pelo instalador oficial da
Microsoft, **assinado digitalmente** e registrado como aplicativo do sistema — não depende do
mesmo mecanismo de manifesto privado que o Chromium avulso do Playwright usa. Isso isola o
problema especificamente à forma como **esse Windows resolve a ativação de um binário Chromium
não assinado implantado via xcopy** — não ao Playwright, não ao código do projeto, e não a uma
corrupção geral do sistema (já que o `sfc` "consertou" algo, mas não o problema em si). A causa
exata dentro do subsistema WinSxS não foi identificada até o nível de detalhe máximo (isso
exigiria uma sessão de rastreamento `sxstrace` com privilégio elevado), mas o comportamento foi
isolado e contornado com uma solução legítima do próprio Playwright, sem exigir nenhuma
alteração de configuração de segurança do sistema.

**A correção usada:** defina `RPA_BROWSER_CHANNEL=msedge` para usar o Microsoft Edge em vez do
Chromium isolado do Playwright:

```bash
# PowerShell
$env:RPA_BROWSER_CHANNEL = "msedge"; python main.py

# bash
RPA_BROWSER_CHANNEL=msedge python main.py
```

Sem essa variável definida, o projeto continua usando o Chromium baixado pelo Playwright — que é
o comportamento padrão recomendado, por não depender de nenhum navegador pré-instalado na
máquina de quem for avaliar o projeto. A variável existe justamente para contornar essa
particularidade pontual de ambiente sem comprometer a portabilidade padrão do projeto.

## O que o script faz

1. Abre `https://rpachallenge.com/` e baixa o `challenge.xlsx`.
2. Lê o Excel com pandas: aplica `strip()` nos cabeçalhos (a coluna `Last Name ` vem com espaço
   no final), ignora a 8ª coluna vazia/fantasma, remove linhas totalmente vazias (o arquivo
   declara ~999 linhas no metadado, mas só ~10 têm dados reais) e converte `Phone Number`
   (que vem como número) para texto.
3. Valida que as 7 colunas obrigatórias existem antes de começar; se faltar alguma, a execução
   é interrompida com um erro claro (`ExcelValidationError`).
4. Clica em Start e percorre uma linha por vez, preenchendo cada campo pelo `ng-reflect-name`
   e enviando o formulário.
5. Espera a tela `.congratulations` aparecer e registra a mensagem de resultado (taxa de sucesso
   e tempo, fornecidos pelo próprio site).
6. Salva um screenshot da tela final em `evidencias/resultado-python.png` (na raiz do repositório).

## Estrutura do código

- `src/constants.py` — URL do desafio e `FIELD_MAP` (coluna do Excel → `ng-reflect-name`).
- `src/excel_reader.py` — leitura e validação do Excel (`read_challenge_data`).
- `src/browser_automation.py` — todas as interações com a página: abrir o site, baixar o Excel,
  clicar em Start, preencher um campo (`fill_field`, função pequena e isolada), preencher uma
  rodada inteira, enviar, esperar a tela final e capturar o resultado.
- `src/logger_config.py` — configura logging em arquivo (`logs/execucao.log`) e console.
- `main.py` — orquestra o fluxo do início ao fim.

## Erros e logs

**Logger único e compartilhado.** `src/logger_config.py` configura um logger chamado
`"rpa_challenge"` com dois handlers: um `FileHandler` gravando em `python/logs/execucao.log`
(UTF-8) e um `StreamHandler` para o console, ambos com o mesmo formato
(`%(asctime)s | %(levelname)-8s | %(message)s`). `main.py` obtém esse logger chamando
`configure_logging(LOG_PATH)`; `src/browser_automation.py` obtém a mesma instância diretamente
via `logging.getLogger("rpa_challenge")` (linha 14) — ou seja, os dois módulos escrevem no
mesmo arquivo e console sem precisar passar o logger como parâmetro. `logger.handlers.clear()`
(linha 14 de `logger_config.py`) garante que handlers não se acumulem se `configure_logging` for
chamado mais de uma vez no mesmo processo.

**Granularidade por rodada e por campo.** Cada rodada é anunciada antes de começar
(`logger.info("Preenchendo rodada %d/%d", ...)`, `main.py` linha 64). Se qualquer coisa dentro
dela falhar, `main.py` (linhas 66-70) loga `"Falha na rodada %d/%d"` com o número exato antes de
repropagar a exceção. Dentro da rodada, `fill_round` em `src/browser_automation.py` (linhas
60-76) preenche cada campo dentro do seu próprio `try/except`, e se um campo específico falhar,
loga `"Falha ao preencher o campo '%s' (ng-reflect-name=%s)"` com o nome da coluna e o atributo
usado como seletor — assim um erro aponta direto para a rodada *e* o campo, sem precisar
inspecionar screenshots ou re-executar com breakpoints para achar o ponto de falha.

**Exemplo real de log** (execução completa, `python/logs/execucao.log`):

```
2026-08-27 10:42:11 | INFO     | === Iniciando automação do RPA Challenge ===
2026-08-27 10:42:16 | INFO     | Site do desafio aberto: https://rpachallenge.com/
2026-08-27 10:42:17 | INFO     | Arquivo Excel baixado em: ...\python\data\challenge.xlsx
2026-08-27 10:42:17 | INFO     | 10 linha(s) válida(s) encontradas no Excel
2026-08-27 10:42:17 | INFO     | Rodadas iniciadas (botão Start clicado)
2026-08-27 10:42:17 | INFO     | Preenchendo rodada 1/10
...
2026-08-27 10:42:18 | INFO     | Preenchendo rodada 10/10
2026-08-27 10:42:18 | INFO     | Desafio concluído: Your success rate is 100% ( 70 out of 70 fields) in 864 milliseconds
2026-08-27 10:42:18 | INFO     | Screenshot do resultado salvo em: ...\evidencias\resultado-python.png
2026-08-27 10:42:18 | INFO     | === Execução finalizada com sucesso ===
```

**Tratamento de erro e código de saída.** `main.py` tem dois blocos `except` no fluxo principal
(linhas 77-82): um específico para `ExcelValidationError` (Excel sem as colunas obrigatórias) e
um genérico para qualquer outra `Exception` (campo não encontrado, timeout esperando a tela
final, etc.). Os dois casos chamam `logger.exception(...)` — que grava a mensagem e o stack
trace completo — e retornam `1` como código de saída do processo (`sys.exit(main())`, última
linha do arquivo). Em execução bem-sucedida, o código de saída é `0`. Não há retry automático em
nenhum ponto: qualquer falha interrompe a execução imediatamente (comportamento fail-fast),
decisão deliberada para um desafio de validação onde mascarar uma falha com uma nova tentativa
esconderia o problema real em vez de expô-lo no log. Um bloco `finally` (linha 83) garante que
`chromium.close()` rode sempre, com sucesso ou falha, para não deixar o processo do navegador
pendurado.

## Dificuldades e limitações

### Dificuldades encontradas e como foram resolvidas

- **Campos que trocam de posição a cada rodada.** Um seletor por posição/índice ou por ordem de
  tabulação quebraria a cada rodada, já que o layout embaralha os campos. A solução foi inspecionar
  o DOM ao vivo no navegador antes de escrever qualquer seletor e descobrir que cada `<input>`
  expõe o atributo `ng-reflect-name` (ex.: `labelFirstName`), gerado pelo Angular em modo
  desenvolvimento, que identifica o campo pelo significado e não muda entre rodadas. Esse atributo
  virou a base do `FIELD_MAP` em `src/constants.py` e do seletor usado em `fill_field`
  (`src/browser_automation.py`, linha 56).
- **Cabeçalho `"Last Name "` com espaço no final.** O nome da coluna no Excel não bate
  exatamente com a string esperada em `EXPECTED_COLUMNS`. Resolvido aplicando `.strip()` em todos
  os cabeçalhos antes de qualquer comparação (`excel_reader.py`, linha 28), então a validação de
  colunas e o acesso via `df[EXPECTED_COLUMNS]` funcionam independentemente de espaços extras.
- **8ª coluna fantasma no Excel.** O arquivo baixado do site traz uma coluna a mais, sem uso, além
  das 7 esperadas. Resolvido selecionando explicitamente `df[EXPECTED_COLUMNS]` (linha 36), que
  ignora qualquer coluna fora dessa lista, em vez de assumir que todas as colunas do arquivo são
  válidas.
- **~999 linhas declaradas no metadado do Excel, só ~10 com dado real.** O `challenge.xlsx`
  declara uma área usada bem maior do que os dados reais (comum em planilhas exportadas/geradas
  dinamicamente). Resolvido com `dropna(how="all")` (linha 36), que descarta qualquer linha
  totalmente vazia antes de contar as linhas válidas — sem esse filtro, `len(data)` incluiria
  centenas de linhas fantasma e a comparação com `TOTAL_ROUNDS` em `main.py` (linha 54) ficaria
  sem sentido.
- **Telefone chegando como número, não como texto.** O pandas lê a coluna "Phone Number" como
  `float` (ex.: `619123456.0`), já que o Excel armazena números sem formatação de texto. Preencher
  o campo com esse valor diretamente introduziria um `.0` indevido no formulário. Resolvido pela
  função `_normalize_phone` (`excel_reader.py`, linhas 42-47), que detecta o caso de float inteiro
  (`value.is_integer()`) e converte para `int` antes de `str()`, produzindo `"619123456"`.

### Limitações conhecidas

- **Dependência do modo desenvolvimento do Angular.** A estratégia de localização por
  `ng-reflect-*` (ver "Como os campos dinâmicos foram identificados") só funciona porque o site
  roda Angular 7 em modo desenvolvimento. Se o site passar a rodar em modo produção, esses
  atributos somem e seria necessário trocar a estratégia de seletor — por exemplo, para XPath por
  `<label>` (`//label[normalize-space()='First Name']/following-sibling::input`). Esse é o maior
  risco de robustez do projeto, documentado aqui como limitação conhecida, não como bug.
- **Número de rodadas e nomes de campo fixos.** `TOTAL_ROUNDS` (10) e `FIELD_MAP` (7 campos
  específicos) em `src/constants.py` são fixos. Se o Excel tiver um número de linhas diferente de
  10, o script apenas registra um aviso e continua (`main.py`, linhas 54-59) — ele não trava, mas
  também não se adapta automaticamente a um número diferente de campos ou a colunas com nomes
  diferentes dos mapeados; isso exigiria atualizar `FIELD_MAP` manualmente.
- **Sem retry automático.** Por design (ver seção "Erros e logs"), qualquer falha pontual — uma
  rede lenta, um campo que demorou um instante a mais para aparecer — interrompe a execução
  inteira em vez de tentar novamente. Isso é intencional para não mascarar falhas, mas significa
  que uma instabilidade transitória do site exige rodar o script de novo manualmente.
- **Ruído esperado no console do navegador.** Mensagens como 404 de fonte, bloqueio de beacon do
  Cloudflare ou o aviso "Form submission canceled..." aparecem no console do navegador durante a
  execução normal, não têm relação com a automação em si e não são tratadas como falha.

## Como rodar os testes

Os testes unitários (`python/tests/`) não abrem navegador nem acessam a rede: usam
`unittest.mock` para simular o `Page` do Playwright e arquivos `.xlsx` temporários (via
pandas/openpyxl) para `excel_reader`. Instale as dependências de desenvolvimento e rode:

```bash
cd python
python -m pip install -r requirements-dev.txt
python -m pytest
```
