"""Constantes usadas pela automação do RPA Challenge."""

CHALLENGE_URL = "https://rpachallenge.com/"

# Mapa: nome da coluna no Excel (após strip) -> valor do atributo
# ng-reflect-name do input correspondente no formulário.
# Esse atributo é exposto pelo Angular em modo desenvolvimento e não muda
# entre rodadas, mesmo com os campos trocando de posição na tela.
FIELD_MAP = {
    "First Name": "labelFirstName",
    "Last Name": "labelLastName",
    "Company Name": "labelCompanyName",
    "Role in Company": "labelRole",
    "Address": "labelAddress",
    "Email": "labelEmail",
    "Phone Number": "labelPhone",
}

EXPECTED_COLUMNS = list(FIELD_MAP.keys())

TOTAL_ROUNDS = 10
