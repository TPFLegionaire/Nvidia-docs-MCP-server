flowchart TD
  Start[Start Application] --> EntryChoice{Access via Browser or API Client}
  EntryChoice -->|Browser| SwaggerUI[Swagger UI at /docs]
  EntryChoice -->|API Client| Login[Call /login Endpoint]
  Login --> CredentialsCheck{Credentials Valid}
  CredentialsCheck -->|Yes| Token[JWT Token Returned]
  CredentialsCheck -->|No| AuthError[Authentication Failed]
  AuthError --> End[End]
  Token --> SwaggerUI
  SwaggerUI --> RegisterREST[POST /mcp/register]
  RegisterREST -->|Success| SendREST[POST /mcp/send]
  RegisterREST -->|Auth Error| AuthError
  SendREST --> ReceiveREST[GET /mcp/receive]
  ReceiveREST --> End
  Token --> RegisterGRPC[gRPC RegisterClient]
  RegisterGRPC --> SendGRPC[gRPC SendMessage]
  SendGRPC --> ReceiveGRPC[gRPC ReceiveMessages]
  ReceiveGRPC --> End
  SwaggerUI --> Docs[Static Docs at /docs/index.html]
  Docs -->|Found| End
  Docs -->|Not Found| Docs404[Documentation Not Found]
  Docs404 --> End
  End --> AdminChoice{Administrator Action}
  AdminChoice -->|Edit Config| EditConfig[Modify config or env vars]
  AdminChoice -->|No Action| End
  EditConfig --> Restart{Restart Server}
  Restart -->|Success| End
  Restart -->|Failure| ReloadError[Config Reload Failed]
  ReloadError --> End