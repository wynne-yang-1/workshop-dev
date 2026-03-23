# Lab 4: Expose the OIC API Through Traefik Hub

## Introduction

Now that your OIC Weather API is active, it's time to expose it through Traefik Hub. In this lab, you will create the Kubernetes resources that route external requests through Traefik Hub to your OIC instance. This includes an ExternalName service pointing to OIC, path rewriting middleware to map a clean virtual endpoint to the long OIC integration URL, and an IngressRoute that ties everything together.

The key architectural concept here is **virtual endpoints**: external consumers call a simple, clean URL like `/weather`, and Traefik Hub transparently rewrites the path to the complex OIC integration URL behind the scenes. Consumers never need to know the underlying OIC path structure.

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Create an ExternalName service pointing to your OIC instance
2. Configure path rewriting middleware to create a clean virtual endpoint
3. Create an API definition for the OIC Weather API
4. Deploy an IngressRoute to route traffic through Traefik Hub to OIC
5. Verify the routing configuration

### Prerequisites

This lab assumes you have:

* Completed the previous labs
* Your OIC instance hostname (e.g., `your-oic-instance.integration.oraclecloud.com`)
* Your OIC integration path (captured in Lab 3, Task 5)
* Your `EXTERNAL_IP` environment variable set from Lab 1

## Task 1: Create the ExternalName Service for OIC

Create a Kubernetes service that points to your OIC instance.

1. Replace `your-oic-instance.integration.oraclecloud.com` with your actual OIC hostname and apply:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Service
    metadata:
      name: oic-backend
      namespace: apps
    spec:
      type: ExternalName
      externalName: your-oic-instance.integration.oraclecloud.com
      ports:
        - port: 443
    EOF
    ```

    > **How does this work?** The ExternalName service creates a DNS alias within Kubernetes that points to your OIC hostname. This allows Traefik Hub to route traffic to OIC as if it were an in-cluster service, even though OIC runs outside the Kubernetes cluster.

## Task 2: Configure Path Rewriting Middleware

OIC integration URLs are long and complex. For example:

```
/ic/api/integration/v2/flows/rest/WEATHER_BY_CITY/1.0/weather
```

Path rewriting lets you expose a clean, developer-friendly path like `/weather` instead.

1. Apply the path rewriting middleware. Adjust the `replacement` path to match your specific OIC integration path from Lab 3, Task 5:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: traefik.io/v1alpha1
    kind: Middleware
    metadata:
      name: virtualendpoint-oic-weather
      namespace: apps
    spec:
      replacePathRegex:
        regex: "^/weather(/.*)?$"
        replacement: "/ic/api/integration/v2/flows/rest/WEATHER_BY_CITY/1.0/weather\$1"
    EOF
    ```

    > **What does the regex do?** It captures `/weather` and any trailing path segments, then rewrites the full path to the OIC integration URL. The `$1` preserves any trailing segments (e.g., query parameters pass through automatically).

## Task 3: Define the OIC Weather API

Create the API resource that defines how your OIC Weather API appears in the Traefik Hub catalog and portal.

1. Apply the API definition:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: API
    metadata:
      name: oic-weather-api
      namespace: apps
    spec:
      title: "OIC Weather API"
      description: "Weather reporting API powered by Oracle Integration Cloud. Returns current weather data including temperature, conditions, and coordinates for any city."
      openApiSpec:
        override:
          servers:
            - url: https://${EXTERNAL_IP}/weather/
    EOF
    ```

    > **Tip:** For a richer portal experience, you can provide a full OpenAPI spec URL in the `openApiSpec.url` field. If you have an OpenAPI JSON or YAML file for your weather integration, host it in a repository and reference it here.

<!-- AUTHOR NOTE:
     Consider creating an OpenAPI spec file for the Weather By City integration
     and hosting it on GitHub, similar to the httpbin spec used in Lab 2. This
     provides a richer experience in the developer portal with documented
     endpoints, parameters, and response schemas.
-->

## Task 4: Create the IngressRoute

Tie everything together with an IngressRoute that chains the path rewriting middleware and routes traffic to OIC.

1. Apply the IngressRoute:

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
    EOF
    ```

    > **Important:** The `passHostHeader: false` setting is critical. Without it, Traefik would forward its own hostname to OIC, which would reject the request. Setting this to `false` ensures the OIC hostname from the ExternalName service is used instead.

## Task 5: Verify the Routing Configuration

Test that requests flow through Traefik Hub toward OIC.

1. Send a test request:

    ```bash
    curl -k "https://${EXTERNAL_IP}/weather?city=Seattle"
    ```

2. At this stage, the request will likely return an authentication error from OIC — **this is expected**. OIC requires an OAuth2.0 token, which you will configure in the next lab.

3. Verify the following:
    - The request reaches Traefik Hub — check the [Traefik Hub dashboard](https://hub.traefik.io) for incoming requests under your gateway.
    - The path rewriting is working — the request should be forwarded to the correct OIC integration URL (visible in the dashboard's request details).

    > **Troubleshooting:** If you see a `404` error instead of an auth error, double-check that your path rewriting regex matches your OIC integration path. If you see a connection error, verify that your ExternalName service hostname is correct.

## Lab 4 Recap

In this lab you created the routing bridge between Traefik Hub and your OIC backend:

* Created an **ExternalName service** (`oic-backend`) that points Kubernetes DNS at your OIC instance hostname.
* Configured a **replacePathRegex middleware** that rewrites the clean `/weather` path to the full OIC integration URL, creating a virtual endpoint.
* Defined an **API** resource (`oic-weather-api`) that represents the weather API in the Traefik Hub catalog.
* Deployed an **IngressRoute** that chains the path rewriting middleware and forwards traffic to OIC with `passHostHeader: false`.
* Verified that requests reach Traefik Hub and are routed toward OIC (authentication will be configured in the next lab).

You may now proceed to the next lab.

## Learn More

* [Traefik Hub — External API Management](https://doc.traefik.io/traefik-hub/api-management/external-api)
* [Securing Oracle Integration Cloud APIs with Traefik on OKE (Carlos Villanua)](https://carlosvillanua.com/securing-oracle-integration-cloud-apis-with-traefik-on-oke/)
* [Traefik — ReplacePathRegex Middleware](https://doc.traefik.io/traefik/middlewares/http/replacepathregex/)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
