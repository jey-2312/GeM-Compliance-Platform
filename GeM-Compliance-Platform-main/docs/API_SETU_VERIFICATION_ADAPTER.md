# Verification Connector / API Setu Notes

The prototype uses mock verification connectors. They are **not** live API Setu
calls and must not be presented as government verification.

API Setu's official documentation describes API Setu as an API marketplace and
API gateway. Its documented flow is: discover an API, subscribe to it, obtain
provider/API Setu approval where required, and then receive the documentation
and credentials needed for access. API Setu also documents HTTPS, the provider's
request/response contract, authentication credentials/tokens, rate limits, and
consent requirements where applicable.

The prototype therefore keeps the provider boundary separate:

```text
VerificationConnector
        |
        +-- MockGSTConnector
        +-- MockPANConnector
        +-- MockUdyamConnector
        +-- MockFinancialVerificationConnector

Future (only after authorized access + provider documentation):

VerificationConnector
        |
        +-- ApiSetuGSTConnector
        +-- ApiSetuPANConnector
        +-- ApiSetuUdyamConnector
```

Do **not** hard-code an API endpoint, API key, client ID, or provider-specific
payload based on assumptions. The exact endpoint and schema must come from the
API listing/provider documentation and the credentials issued for the approved
use case.

The shared output remains the `Verification` domain object, so the rule engine
does not care whether the upstream source is a mock or an authorized external
connector.
