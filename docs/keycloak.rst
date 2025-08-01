Keycloak Integration with ZOO-Project
=====================================

This guide documents the integration of Keycloak into the ZOO-Project using a remote or Docker-hosted Keycloak instance. The goal is to secure OGC API endpoints using HTTP Bearer Token authentication.

Overview
--------

ZOO-Project's endpoints like `/ogc-api/jobs`, `/ogc-api/processes`, `/ogc-api/stac`, and `/ogc-api/raster` can be protected using Keycloak-based authentication via the `libapache2-mod-auth-openidc` Apache module.

Two Keycloak clients are required:

1. **API Client** (for Apache to validate Bearer tokens)
2. **Web Client** (for the Nuxt web app to authenticate users and obtain tokens)

Docker Setup
------------

To include Keycloak in the Docker environment:

.. code-block:: yaml

  keycloack:
    image: quay.io/keycloak/keycloak:26.0.7
    command:
      - start-dev
      - --features admin-fine-grained-authz token-exchange
      - --http-enabled=true
      - --verbose
    environment:
      KEYCLOAK_ADMIN_PASSWORD: admin
      KEYCLOAK_ADMIN: admin
    networks:
      front-tier:
        ipv4_address: 172.16.238.18
    ports:
      - "8099:8080"

Keycloak Setup
--------------

**Realm**

- Create a new realm: `zooproject`

**Clients**

1. **API Client**: `apache-zooproject`
   - Enable `Client authentication`
   - Use only for validating Bearer tokens (no login flow)
   - Get `client_secret` from the Credentials tab

2. **Web Client**: `webapp-zooproject`
   - Enable `Client authentication`
   - Enable standard login flow
   - Set:
     - Root URL: `http://<host>:8000`
     - Redirect URIs: `/*`
   - Get `client_secret` from the Credentials tab

Apache Configuration
--------------------

In your `docker/default.conf`, add the following before `</VirtualHost>`:

.. code-block:: apache

  ServerName zoo.something.com

  OIDCProviderIssuer http://<keycloak_host>/realms/zooproject/.well-known/openid-configuration
  OIDCOAuthClientID apache-zooproject
  OIDCOAuthClientSecret <client_secret>
  OIDCOAuthIntrospectionEndpoint http://<keycloak_host>/realms/zooproject/protocol/openid-connect/token/introspect
  OIDCOAuthIntrospectionEndpointAuth client_secret_basic
  OIDCRedirectURI "/"
  OIDCCryptoPassphrase somethingsecure

  <Location "/ogc-api/processes">
    AuthType oauth20
    AuthName "Protected Resource"
    Require valid-user
  </Location>
  <Location "/ogc-api/jobs">
    AuthType oauth20
    AuthName "Protected Resource"
    Require valid-user
  </Location>
  <Location "/ogc-api/stac">
    AuthType oauth20
    AuthName "Protected Resource"
    Require valid-user
  </Location>
  <Location "/ogc-api/raster">
    AuthType oauth20
    AuthName "Protected Resource"
    Require valid-user
  </Location>

Enable required Apache modules in your Dockerfile:

.. code-block:: dockerfile

  && a2enmod cgi rewrite headers auth_openidc proxy proxy_http \

Web Client Setup (Nuxt + Docker)
--------------------------------

Use the Nuxt client from:

- https://github.com/Wagtial/zooproject-nuxt-client

Create `.env` file from `env_sample` and configure:

.. code-block:: bash

  NUXT_OIDC_ISSUER=http://<keycloak_host>/realms/zooproject
  NUXT_OIDC_CLIENT_ID=webapp-zooproject
  NUXT_OIDC_CLIENT_SECRET=<secret>
  NUXT_ZOO_BASEURL=http://<zoo_host>
  NUXT_BASE_URL=http://<nuxt_host>:8000
  AUTH_ORIGIN=http://<nuxt_host>:8000
  NUXT_AUTH_SECRET=some-secret
  NEXTAUTH_URL=http://<nuxt_host>:8000
  ZOO_OGCAPI_REQUIRES_BEARER_TOKEN=true
  NODE_ENV=production

**Dockerfile updates**:

.. code-block:: dockerfile

  && echo "Listen 8000" >> /etc/apache2/ports.conf \
  && cp /000-nuxtclient.conf /etc/apache2/sites-available/

Example `nuxtclient.conf` vhost block:

.. code-block:: apache

  <VirtualHost *:8000>
    ServerName nuxt.zoo
    <Location "/">
      ProxyPass http://172.16.238.17:3000/
      ProxyPassReverse http://172.16.238.17:3000/
    </Location>
  </VirtualHost>

Ensure the required Apache modules are enabled (as above).

Configuration Files
-------------------

**main.cfg** (required headers)

.. code-block:: ini

  [headers]
  Access-Control-Allow-Origin=*
  Access-Control-Allow-Methods=GET, POST, PUT, PATCH, OPTIONS, DELETE, HEAD
  Access-Control-Allow-Headers=Content-Type, Accept, Authorization, Origin

**oas.cfg** (check rootHost/rootUrl)

- Make sure they point to the public Zoo server domain or IP.

Deploy with Docker Compose
--------------------------

Clone the OIDC branch:

.. code-block:: bash

  git clone https://github.com/Wagtial/ZOO-Project -b oidc

Build Zoo Project:

.. code-block:: bash

  docker build . \
    --build-arg SERVER_URL=http://<ip> \
    --build-arg WS_SERVER_URL=ws://<ip> \
    -t zooproject/zoo-project:latest \
    --no-cache

Build Nuxt client:

.. code-block:: bash

  cp docker/env_nuxt.sample docker/.env_nuxt
  docker compose build --no-cache nuxtclient

Bring up all services:

.. code-block:: bash

  docker compose up -d --remove-orphans

