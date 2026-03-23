# Lab 6: (Optional) Working with Plans, Catalog Items, and Bundles

## Introduction

In this optional lab, you will explore Traefik Hub's API lifecycle management features in more depth. You will create additional API plans with different rate limits and quotas, publish them as catalog items for the OIC Weather API, observe rate limiting in action, and explore the Traefik Hub dashboard for monitoring API traffic.

These capabilities are essential for organizations that need to offer tiered API access to different consumer groups — for example, a free tier with strict limits for evaluation, a standard tier for typical usage, and a premium tier for high-volume consumers.

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Create a Silver API plan to add a mid-tier between Gold and Bronze
2. Publish all three tiers as catalog items for the OIC Weather API
3. Test rate limiting by exceeding the Bronze plan's limits
4. Explore the Traefik Hub dashboard for API traffic observability
5. Understand the relationships between API management CRDs

### Prerequisites

This lab assumes you have:

* Completed Labs 1–5
* Your OIC Weather API exposed and secured through Traefik Hub

## Task 1: Create a Silver Plan

Add a mid-tier plan between Gold and Bronze to offer three levels of service.

1. Apply the Silver plan:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: APIPlan
    metadata:
      name: weather-silver-plan
      namespace: apps
    spec:
      title: Silver
      description: "Silver Plan — 10 requests/second, 100K requests/month"
      rateLimit:
        limit: 10
        period: 1s
      quota:
        limit: 100000
        period: 750h
    EOF
    ```

    You now have three tiers of service:

    | Plan | Rate Limit | Monthly Quota |
    |------|-----------|---------------|
    | **Gold** | 100 req/s | 1,000,000 |
    | **Silver** | 10 req/s | 100,000 |
    | **Bronze** | 1 req/s | 1,000 |

## Task 2: Publish Plans as Catalog Items

Make all three tiers available in the portal for the OIC Weather API.

1. Apply the catalog items:

    ```bash
    cat <<EOF | kubectl apply -f -
    apiVersion: hub.traefik.io/v1alpha1
    kind: APICatalogItem
    metadata:
      name: weather-gold-catalog
      namespace: apps
    spec:
      everyone: true
      apis:
        - name: oic-weather-api
      apiPlan:
        name: sample-gold-plan
    ---
    apiVersion: hub.traefik.io/v1alpha1
    kind: APICatalogItem
    metadata:
      name: weather-silver-catalog
      namespace: apps
    spec:
      everyone: true
      apis:
        - name: oic-weather-api
      apiPlan:
        name: weather-silver-plan
    ---
    apiVersion: hub.traefik.io/v1alpha1
    kind: APICatalogItem
    metadata:
      name: weather-bronze-catalog
      namespace: apps
    spec:
      everyone: true
      apis:
        - name: oic-weather-api
      apiPlan:
        name: sample-bronze-plan
    EOF
    ```

2. Open the developer portal at `https://<EXTERNAL_IP>/oci-portal` and verify that the OIC Weather API now shows all three plan options (Gold, Silver, Bronze) in the catalog.

## Task 3: Test Rate Limiting

Subscribe to the Bronze plan (1 request/second) and observe rate limiting in action.

1. In the developer portal, create a new **Application** and **subscribe** to the **Bronze** plan.

2. Send multiple rapid requests to observe rate limiting:

    ```bash
    for i in {1..5}; do
      curl -s -o /dev/null -w "Request ${i}: HTTP %{http_code}\n" \
        -k "https://${EXTERNAL_IP}/weather?city=Seattle" \
        -H "Authorization: Bearer <your-jwt-token>"
    done
    ```

3. You should see output similar to:

    ```
    Request 1: HTTP 200
    Request 2: HTTP 429
    Request 3: HTTP 429
    Request 4: HTTP 429
    Request 5: HTTP 429
    ```

    The first request succeeds, and subsequent requests that exceed the 1 request/second limit receive a `429 Too Many Requests` response. Redis tracks the rate counters across the cluster, ensuring consistent enforcement even if Traefik Hub is scaled to multiple replicas.

## Task 4: Explore the Traefik Hub Dashboard

1. Log in to [hub.traefik.io](https://hub.traefik.io).
2. Navigate to **APIs** to see all registered APIs, their status, and associated routes. You should see both the sample API from Lab 2 and the OIC Weather API from Lab 4.
3. Navigate to **Gateways** to view your OKE gateway's health and traffic metrics.
4. Explore the **API Portal** management section to see applications, subscriptions, and usage data.
5. Review the request logs to see how your test requests were processed, including which were allowed and which were rate-limited.

    > **Key takeaway:** Every resource you created with `kubectl apply` in this workshop is visible and manageable in the Traefik Hub dashboard. This dual management model — declarative CRDs for automation and a web dashboard for visibility — is a core strength of Traefik Hub's approach.

## Task 5: Understanding the CRD Relationships

Here is how the Traefik Hub CRDs relate to each other:

| CRD | Purpose | Created By |
|-----|---------|------------|
| **API** | Defines the API itself (title, description, OpenAPI spec). Linked to IngressRoutes via annotations. | Platform team (YAML) |
| **APIPlan** | Defines rate limits and quotas for a tier of service. | Platform team (YAML) |
| **APICatalogItem** | Links an API to a Plan, making it available in the portal catalog. Controls visibility (everyone, specific groups, etc.). | Platform team (YAML) |
| **APIPortal** | The developer portal interface. Can contain multiple APIs and plans. | Platform team (YAML) |
| **Application** | Represents a consuming application. | Developers (Portal UI) |
| **Subscription** | Links an Application to a specific APICatalogItem (API + Plan combination). | Developers (Portal UI) |

This declarative model means your entire API management configuration can be version-controlled in Git and deployed through CI/CD pipelines — the GitOps approach. Platform teams define the APIs, plans, and catalog in YAML; developers self-serve through the portal.

## Lab 6 Recap

In this optional lab you explored Traefik Hub's API lifecycle management capabilities:

* Created a **Silver APIPlan** to add a mid-tier between Gold and Bronze, giving you three levels of service with progressively stricter rate limits and quotas.
* Published all three tiers as **APICatalogItem** resources, making them available for subscription in the developer portal.
* Tested **rate limiting** by exceeding the Bronze plan's 1 req/s limit and observing `429 Too Many Requests` responses.
* Explored the **Traefik Hub dashboard** for observability into API traffic, gateway health, and subscription management.
* Mapped out the **CRD relationships** that power the declarative, GitOps-friendly API management model.

You may now proceed to Clean Up.

## Learn More

* [Traefik Hub — API Management Overview](https://doc.traefik.io/traefik-hub/api-management/apim-overview)
* [Traefik Hub — Getting Started Quick Start Guide](https://doc.traefik.io/traefik-hub/api-management/quick-start-guide)
* [Traefik Hub — Distribute Rate Limits](https://doc.traefik.io/traefik-hub/operations/distributed-rate-limit)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
