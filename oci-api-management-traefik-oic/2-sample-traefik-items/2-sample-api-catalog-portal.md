# Lab 2: Deploy Traefik's Sample API with Catalog and Portal

## Introduction

Before working with OIC, let's get familiar with Traefik Hub's API management capabilities by deploying a sample API. In this lab, you will create a simple external API, publish it to a catalog with tiered plans, and set up a developer portal — all using Kubernetes CRDs. This gives you a hands-on foundation for the workflows you will use with OIC in later labs.

Think of this lab as a quick win: by the end, you will have a fully functional API management setup running on OKE, with a developer portal where consumers can browse APIs, subscribe to plans, and test endpoints.

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Create an application namespace for your API resources
2. Deploy a sample external API using Traefik Hub CRDs
3. Install Redis for API plan rate limiting and quota enforcement
4. Create tiered API plans (Gold and Bronze)
5. Set up an API Portal with catalog items
6. Test the API through the developer portal

### Prerequisites

This lab assumes you have:

* Completed Lab 1 (OKE cluster and Traefik Hub deployed)
* Your `EXTERNAL_IP` environment variable set from Lab 1

## Task 1: Create the Application Namespace

Create a namespace to house your API resources. All CRDs you create in this workshop will live in this namespace.

1. Run the following command:

    ```bash
    kubectl create namespace apps
    ```

## Task 2: Deploy the Sample ExternalName Service

For this sample, you will use `httpbin.org` as a simple external backend to demonstrate the routing pattern. Later, you will replace this with your OIC endpoint.

1. Apply the ExternalName service:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: Service
    metadata:
      name: oci-svc
      namespace: apps
    spec:
      type: ExternalName
      externalName: httpbin.org
      ports:
        - port: 443
    EOF
    ```

    > **What is an ExternalName service?** It creates a DNS alias within Kubernetes that points to an external hostname. This allows Traefik Hub to route traffic to external services as if they were in-cluster.

## Task 3: Deploy the API Definition, IngressRoute, and Middleware

Define the API resource, routing rules, and path stripping middleware in a single apply:

1. Create the API definition:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: API
    metadata:
      name: traefik-sample-api
      namespace: apps
    spec:
      title: "Traefik Sample API"
      description: "Sample API for demonstrating Traefik Hub API management on OKE"
      openApiSpec:
        url: https://raw.githubusercontent.com/carlosvillanua/apidefinitions/refs/heads/master/httpbinoas.json
        override:
          servers:
            - url: https://${EXTERNAL_IP}/sample/
    EOF
    ```

2. Create the strip-prefix middleware and IngressRoute:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: traefik.io/v1alpha1
    kind: Middleware
    metadata:
      name: stripprefix-sample
      namespace: apps
    spec:
      stripPrefix:
        prefixes:
          - /sample
          - /oci-portal
    ---
    apiVersion: traefik.io/v1alpha1
    kind: IngressRoute
    metadata:
      name: traefik-sample-route
      namespace: apps
      annotations:
        hub.traefik.io/api: traefik-sample-api@apps
    spec:
      entryPoints:
        - websecure
      routes:
        - match: PathPrefix(`/sample`)
          services:
            - name: oci-svc
              port: 443
              passHostHeader: false
          middlewares:
            - name: stripprefix-sample
    EOF
    ```

## Task 4: Install Redis for API Plans

API Plans require Redis for distributed rate limiting and quota management.

> **Note:** If Redis was already installed as part of your Marketplace deployment, skip this task.

1. Install Redis:

    ```bash
    helm install redis oci://registry-1.docker.io/cloudpirates/redis -n traefik --wait
    ```

2. Get the Redis password and update Traefik Hub:

    ```bash
    export REDIS_PASSWORD=$(kubectl get secret redis -n traefik -o jsonpath="{.data.redis-password}" | base64 -d)

    helm upgrade traefik -n traefik --wait \
      --reset-then-reuse-values \
      --set hub.redis.endpoints=redis.traefik.svc.cluster.local:6379 \
      --set hub.redis.password=${REDIS_PASSWORD} \
      traefik/traefik
    ```

> **Note:** This Redis installation is for demonstration purposes only and uses basic configuration. For production deployments, configure Redis with appropriate security, persistence, and high availability settings.

## Task 5: Create API Plans and Catalog Items

1. Define Gold and Bronze plans with different rate limits:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: APIPlan
    metadata:
      name: sample-gold-plan
      namespace: apps
    spec:
      title: Gold
      description: "Gold Plan — 100 requests/second, 1M requests/month"
      rateLimit:
        limit: 100
        period: 1s
      quota:
        limit: 1000000
        period: 750h
    ---
    apiVersion: hub.traefik.io/v1alpha1
    kind: APIPlan
    metadata:
      name: sample-bronze-plan
      namespace: apps
    spec:
      title: Bronze
      description: "Bronze Plan — 1 request/second, 1K requests/month"
      rateLimit:
        limit: 1
        period: 1s
      quota:
        limit: 1000
        period: 750h
    EOF
    ```

2. Publish these plans as catalog items:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: APICatalogItem
    metadata:
      name: sample-gold-catalog
      namespace: apps
    spec:
      everyone: true
      apis:
        - name: traefik-sample-api
      apiPlan:
        name: sample-gold-plan
    ---
    apiVersion: hub.traefik.io/v1alpha1
    kind: APICatalogItem
    metadata:
      name: sample-bronze-catalog
      namespace: apps
    spec:
      everyone: true
      apis:
        - name: traefik-sample-api
      apiPlan:
        name: sample-bronze-plan
    EOF
    ```

## Task 6: Create the API Portal

Deploy a developer portal to provide a self-service interface for API consumers.

1. Create the portal and its routing:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: APIPortal
    metadata:
      name: oci-portal
      namespace: apps
    spec:
      title: "OCI Workshop Portal"
      description: "API Portal for the Traefik + OIC Workshop"
      trustedUrls:
        - https://${EXTERNAL_IP}/oci-portal
    ---
    apiVersion: traefik.io/v1alpha1
    kind: IngressRoute
    metadata:
      name: oci-portal-route
      namespace: apps
      annotations:
        hub.traefik.io/api-portal: oci-portal@apps
    spec:
      entryPoints:
        - websecure
      routes:
        - match: PathPrefix(`/oci-portal`)
          kind: Rule
          middlewares:
            - name: stripprefix-sample
              namespace: apps
          services:
            - name: apiportal
              namespace: traefik
              port: 9903
    EOF
    ```

## Task 7: Test in the Developer Portal

1. Open your browser and navigate to `https://<EXTERNAL_IP>/oci-portal`.
2. Sign in (or create an account if using API key authentication at this stage).
3. Browse the **API Catalog** — you should see the "Traefik Sample API" listed with Gold and Bronze plans.
4. Create an **Application**, then **subscribe** to one of the plans.
5. Use the portal's built-in testing interface to send a test request to the sample API.
6. Verify you receive a successful response from the httpbin backend.

## Lab 2 Recap

In this lab you stood up a complete API management workflow using only Kubernetes CRDs:

* Created an **ExternalName service** to route traffic to an external backend.
* Defined an **API** resource with an OpenAPI spec, making it discoverable in the Traefik Hub catalog.
* Created an **IngressRoute** with path-stripping **Middleware** to expose a clean URL.
* Installed **Redis** for distributed rate limiting.
* Created **APIPlan** resources (Gold and Bronze) with different rate limits and quotas.
* Published **APICatalogItem** resources to make the plans available in the portal.
* Deployed an **APIPortal** and tested the full self-service experience.

Every one of these resources is declarative YAML — version-controllable, CI/CD-friendly, and reproducible. In the next labs, you will swap the sample backend for a real OIC integration.

You may now proceed to the next lab.

## Learn More

* [Traefik Hub — Integrating External APIs with OCI](https://doc.traefik.io/traefik-hub/operations/oracle-oci/external-api-integration)
* [Traefik Hub — API Management Overview](https://doc.traefik.io/traefik-hub/api-management/apim-overview)
* [Traefik Hub — Getting Started Quick Start Guide](https://doc.traefik.io/traefik-hub/api-management/quick-start-guide)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
