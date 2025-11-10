## 1. System Architecture Overview

The system is organized as a standard web application with three main layers:

1. **Client Layer (Presentation)**  
   - Runs in the user’s browser or as a thin UI.  
   - Talks to the backend over HTTP/HTTPS (usually JSON).  
   - 🟣 TODO: replace with actual client (e.g. React, plain HTML, Vue).

2. **Application / API Layer (Backend Services)**  
   - Exposes RESTful (or GraphQL) endpoints to the client.  
   - Implements business logic for the domain “Synergy”.  
   - Orchestrates persistence and any external integrations.  
   - 🟣 TODO: replace with actual backend tech (e.g. Node/Express, Spring Boot, Django).

3. **Data & Integration Layer**  
   - Persists application data.  
   - Optionally integrates with 3rd-party services (auth, payments, storage, etc.).  
   - 🟣 TODO: replace with actual database (e.g. MySQL, PostgreSQL, MongoDB).

At a high level:

```text
[ Client (Web/UI) ]
          |
          v
[ Backend / API ]
          |
          v
[ Database(s) + External Services ]