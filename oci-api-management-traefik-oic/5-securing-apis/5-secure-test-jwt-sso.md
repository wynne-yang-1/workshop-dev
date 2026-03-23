# Lab 5: Secure and Test the API with JWT and SSO

## Introduction

In this lab, you will configure the security layer that bridges external client authentication with OIC's backend authentication requirements. This is the key architectural pattern of the workshop: external clients authenticate with their own JWT tokens (validated via Oracle Identity Domains' JWKS endpoint), while Traefik Hub transparently handles the OIC-specific OAuth2.0 token exchange behind the scenes. External consumers never need OIC credentials.

You will set up three security components: JWT validation for inbound requests, OAuth2.0 Client Credentials middleware for the OIC backend hop, and OIDC-based SSO for the developer portal.

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Configure JWT authentication using Oracle Identity Domains (IDCS) JWKS endpoint
2. Store OIC client credentials securely in a Kubernetes Secret
3. Set up OAuth2.0 Client Credentials middleware for OIC backend authentication
4. Update the IngressRoute to include the authentication middleware
5. Enable OIDC-based SSO on the Traefik Hub developer portal
6. Test the complete end-to-end flow

### Prerequisites

This lab assumes you have:

* Completed the previous labs
* Access to your Oracle Identity Domains (IDCS) configuration in the OCI Console
* An OIDC / confidential application registered in Oracle Identity Domains (or the ability to create one)

## Task 1: Configure JWT Validation in Traefik Hub

Traefik Hub needs to know how to validate JWT tokens issued by Oracle Identity Domains.

1. Locate your JWKS URI. You can find this from your Identity Domain's `.well-known/openid-configuration` endpoint. It will look like:

    ```
    https://idcs-XXXXXXXXXX.identity.oraclecloud.com/admin/v1/SigningCert/jwk
    ```

2. In the [Traefik Hub Dashboard](https://hub.traefik.io), navigate to **Auth Settings** > **Gateway** > **JWT**.
3. Set the **Token validation method** to **JWKs URL**.
4. Paste your JWKS URI in the provided field.
5. Click **Save**.

    This configuration ensures that Traefik Hub validates the signature and expiration of incoming JWT tokens against the public keys published by Oracle Identity Domains. Requests with invalid or expired tokens are rejected at the gateway before they ever reach OIC.

    > **Note on API Keys vs JWT:** Once JWT authentication is configured in Traefik Hub, API key-based authentication on the portal is automatically disabled. All API access will require valid JWT tokens. This is by design — JWT provides stronger security guarantees and integrates with your organization's identity provider.

## Task 2: Store OIC Client Credentials

OIC requires its own OAuth2.0 token for API access. Before creating the middleware, store the OIC client credentials securely as a Kubernetes Secret.

1. In the OCI Console, navigate to your **Identity Domain > Integrated Applications**. Locate (or create) a confidential application configured for OIC access. Note the **Client ID**, **Client Secret**, and **Scope**.

2. Create the Kubernetes Secret:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Secret
    type: Opaque
    metadata:
      name: oic-oauth2-creds
      namespace: apps
    stringData:
      clientID: "<your-oic-client-id>"
      clientSecret: "<your-oic-client-secret>"
      scope: "<your-oic-scope>"
    EOF
    ```

    > **Security best practice:** Never embed credentials directly in middleware CRDs. The `urn:k8s:secret:` prefix (used in the next task) tells Traefik Hub to read values from Kubernetes Secrets at runtime.

## Task 3: Create the OAuth2.0 Client Credentials Middleware

Traefik Hub's OAuth2.0 Client Credentials middleware handles the OIC token exchange automatically — obtaining a fresh OIC token for each request using the stored credentials.

1. Create the middleware. Replace the token URL with your Identity Domain's OAuth endpoint:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: traefik.io/v1alpha1
    kind: Middleware
    metadata:
      name: oauth2-oic-backend
      namespace: apps
    spec:
      plugin:
        oAuthClientCredentials:
          url: "https://idcs-XXXXXXXXXX.identity.oraclecloud.com/oauth2/v1/token"
          clientID: urn:k8s:secret:oic-oauth2-creds:clientID
          clientSecret: urn:k8s:secret:oic-oauth2-creds:clientSecret
          scopes:
            - urn:k8s:secret:oic-oauth2-creds:scope
    EOF
    ```

## Task 4: Update the IngressRoute

Update the OIC Weather IngressRoute to include the OAuth2.0 backend middleware:

1. Apply the updated IngressRoute:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: traefik.io/v1alpha1
    kind: IngressRoute
    metadata:
      name: oic-weather-route
      namespace: apps
      annotations:
        hub.traefik.io/api: oic-weather-api@apps
    spec:
      entryPoints:
        - websecure
      routes:
        - match: PathPrefix(`/weather`)
          services:
            - name: oic-backend
              port: 443
              passHostHeader: false
          middlewares:
            - name: virtualendpoint-oic-weather
            - name: oauth2-oic-backend
    EOF
    ```

    > **Middleware execution order:** The JWT validation happens at the Traefik Hub gateway level (configured via the dashboard in Task 1). Then, during request processing, the path rewriting middleware fires first, followed by the OAuth2.0 middleware which obtains a backend token and attaches it to the forwarded request.

## Task 5: Configure SSO on the Developer Portal

Enable Single Sign-On so portal users authenticate with Oracle Identity Domains via OIDC.

1. In the [Traefik Hub Dashboard](https://hub.traefik.io), navigate to **Auth Settings**.
2. In the **Portal** table, select the **OIDC** option.
3. Complete the OIDC configuration form:

    | Field | Value |
    |-------|-------|
    | **Issuer URL** | Your OIDC discovery URL (e.g., `https://idcs-XXXXXXXXXX.identity.oraclecloud.com/.well-known/openid-configuration`) |
    | **Client ID** | From your OCI application registration |
    | **Client Secret** | From your OCI application registration |
    | **Scopes** | `openid email profile` |

4. **Configure the redirect URL in OCI:** In the OCI Console, navigate to your Identity Domain > Integrated Applications. Add the following redirect URL to your application:

    ```
    https://<EXTERNAL_IP>/oci-portal/callback
    ```

5. Click **Save** in the Traefik Hub dashboard.

    After saving, the API Portal login will switch to your Oracle Identity Provider, enabling SSO for all portal users.

## Task 6: Test the End-to-End Flow

**Step 1: Obtain a JWT token from Oracle Identity Domains.**

1. Run the following command, replacing the placeholders with your values:

    ```bash
    curl -X POST \
      "https://idcs-XXXXXXXXXX.identity.oraclecloud.com/oauth2/v1/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "grant_type=client_credentials" \
      -d "client_id=<your-external-client-id>" \
      -d "client_secret=<your-external-client-secret>" \
      -d "scope=<your-scope>"
    ```

2. Copy the `access_token` value from the JSON response.

**Step 2: Call the API through Traefik Hub.**

1. Send the request with your JWT token:

    ```bash
    curl -k "https://${EXTERNAL_IP}/weather?city=Seattle" \
      -H "Authorization: Bearer <your-jwt-token>"
    ```

2. You should receive a JSON response with weather data:

    ```json
    {
      "city": "Seattle",
      "longitude": -122.3321,
      "latitude": 47.6062,
      "country": "US",
      "description": "overcast clouds",
      "temp": 52.3
    }
    ```

**What happened behind the scenes:**

1. Traefik Hub received the request at `/weather?city=Seattle`.
2. JWT middleware validated your token against the IDCS JWKS endpoint.
3. Path rewriting transformed `/weather` to the full OIC integration path.
4. OAuth2.0 middleware obtained a fresh OIC backend token using the stored client credentials.
5. The request was forwarded to OIC with the backend token.
6. OIC executed the Weather By City integration, calling the OpenWeather API.
7. The weather response flowed back through Traefik Hub to your client.

**Step 3: Test through the Developer Portal.**

1. Navigate to `https://<EXTERNAL_IP>/oci-portal`.
2. Sign in using your Oracle Identity Domains credentials (SSO).
3. Browse to the OIC Weather API in the catalog.
4. Create an **Application** and **subscribe** to a plan.
5. Use the portal's built-in testing interface to send a request with your JWT token.

## Lab 5 Recap

In this lab you completed the security architecture:

* Configured **JWT validation** in the Traefik Hub dashboard using your Oracle Identity Domains JWKS endpoint, so all inbound requests are verified before reaching OIC.
* Stored OIC client credentials in a **Kubernetes Secret** and created an **OAuth2.0 Client Credentials middleware** that transparently obtains backend tokens for OIC.
* Updated the **IngressRoute** to chain the path rewriting and OAuth2.0 middlewares.
* Configured **OIDC-based SSO** on the developer portal, so portal users authenticate with Oracle Identity Domains.
* Tested the **complete end-to-end flow**: external JWT authentication → gateway validation → path rewriting → backend token exchange → OIC invocation → response.

The external client and the OIC backend each have their own authentication realm, and Traefik Hub bridges them seamlessly.

You may now proceed to the next lab (optional), or skip to Clean Up.

## Learn More

* [Traefik Hub — JWT Authentication](https://doc.traefik.io/traefik-hub/authentication-authorization/access-overview)
* [Traefik Hub — Oracle IAM Identity Domain Configuration](https://doc.traefik.io/traefik-hub/authentication-authorization/oracle/oci-iam-identity-domain)
* [Traefik Hub — API Portal Authentication](https://doc.traefik.io/traefik-hub/api-management/api-portal-auth)
* [Securing Oracle Integration Cloud APIs with Traefik on OKE (Carlos Villanua)](https://carlosvillanua.com/securing-oracle-integration-cloud-apis-with-traefik-on-oke/)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
