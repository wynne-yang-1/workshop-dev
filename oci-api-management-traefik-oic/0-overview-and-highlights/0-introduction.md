# Introduction: Securing and Managing Oracle Integration Cloud APIs with Traefik Hub on OKE

## Introduction

Organizations using Oracle Integration Cloud (OIC) often build dozens — or even hundreds — of integrations that expose REST APIs. While OIC provides a powerful engine for building these integrations, managing them at scale introduces real challenges: how do you provide consistent security across all your APIs? How do you give developers a self-service portal to discover and subscribe to APIs? How do you enforce rate limits, version APIs, and maintain a centralized catalog — especially when your organization operates across multiple clouds or on-premises environments?

**Traefik Hub** is a Kubernetes-native API management platform that addresses these challenges head-on. Deployed to **Oracle Kubernetes Engine (OKE)** directly from the OCI Marketplace, Traefik Hub acts as a centralized gateway that catalogs, secures, and manages OIC APIs — and any other APIs in your organization — using declarative Kubernetes Custom Resource Definitions (CRDs).

In this workshop, you will build a working API in Oracle Integration Cloud, then deploy and manage that API through Traefik Hub. By the end, you will have a fully functional API management layer running on OKE, complete with JWT-based authentication, a developer portal, and tiered API plans.

**Estimated Workshop Time:** 1 hour 30 minutes (Labs 1–5 + cleanup). Lab 6 is an optional extension.

### Objectives

In this workshop, you will learn how to:

1. Import and activate a pre-built REST API integration in Oracle Integration Cloud
2. Deploy Traefik Hub to Oracle Kubernetes Engine (OKE) using the OCI Marketplace stack
3. Expose an OIC API through Traefik Hub using Kubernetes CRDs (ExternalName Service, IngressRoute, Middleware)
4. Configure JWT authentication using Oracle Identity Domains (IDCS) for external client validation
5. Integrate OCI Single Sign-On (SSO) with Traefik Hub's developer portal via OIDC
6. Create and manage API Plans, Catalog Items, and the API Portal for a self-service developer experience
7. Test the complete end-to-end flow: client authentication, token exchange, API invocation, and response

### Prerequisites

This workshop assumes you have:

* An Oracle Cloud Infrastructure (OCI) tenancy with sufficient privileges to create OKE clusters, manage compartments, and configure Identity Domains
* An active Oracle Integration Cloud (OIC) instance (Generation 3 recommended)
* A Traefik Hub account and license token — [contact Traefik Labs](https://traefik.io/pricing) for a trial license
* Access to the Traefik Hub online dashboard at [hub.traefik.io](https://hub.traefik.io)
* A free API key from [OpenWeather](https://home.openweathermap.org/) (required for the OIC weather integration)
* `kubectl` installed and configured on your local machine
* Basic familiarity with Kubernetes concepts (pods, services, namespaces, CRDs)
* Basic familiarity with Oracle Integration Cloud (projects, integrations, connections)

## Reference Architecture

The architecture for this workshop follows a layered approach:

1. **External clients** send requests with a JWT token obtained from Oracle Identity Domains (IDCS).
2. **Traefik Hub** (running on OKE) validates the JWT using the JWKS endpoint from IDCS.
3. **OAuth2.0 middleware** obtains a fresh access token for OIC backend communication.
4. **Path rewriting** transforms clean, developer-friendly API paths into OIC integration URLs.
5. **The request is forwarded** to OIC with the backend token.
6. **The response** flows back through Traefik Hub to the client.

This pattern decouples external authentication from OIC's own OAuth requirements, meaning external consumers never need OIC credentials. All security is centralized at the gateway layer.

> **Architecture Diagram Placeholder:** Insert diagram showing: External Client → Traefik Hub (OKE) → Oracle Integration Cloud, with Oracle Identity Domains providing JWT/JWKS validation for the external leg and OAuth2.0 tokens for the OIC backend leg.

## Solution Architecture

| Component | Role |
|-----------|------|
| **Oracle Kubernetes Engine (OKE)** | Managed Kubernetes cluster hosting Traefik Hub. Provisioned via the OCI Marketplace stack (Terraform-based). |
| **Traefik Hub** | Kubernetes-native API gateway and management platform. Deployed to OKE via Helm chart from the OCI Marketplace. Handles JWT validation, OAuth2.0 token exchange, path rewriting, rate limiting, and developer portal. |
| **Oracle Integration Cloud (OIC)** | Integration platform hosting the Weather By City REST API. Acts as the backend service that Traefik Hub routes requests to. |
| **Oracle Identity Domains (IDCS)** | Identity provider that issues JWT tokens for external client authentication and provides the JWKS endpoint for token validation. Also serves as the OIDC provider for SSO on the developer portal. |
| **Redis** | In-cluster Redis instance used by Traefik Hub for distributed rate limiting and quota enforcement across API plans. |

## Key Features

### Oracle Integration Cloud (OIC)

Oracle Integration Cloud is a fully managed integration platform that enables you to connect SaaS and on-premises applications, automate business processes, and build APIs. Key capabilities relevant to this workshop include:

1. **REST API creation** — Design and expose REST APIs directly within OIC using the REST Adapter.
2. **Project-based lifecycle management** — Organize integrations, connections, lookups, and libraries within projects for streamlined development and deployment.
3. **Built-in monitoring and observability** — Track integration instances, view activity streams, and monitor business identifiers at runtime.
4. **Export and import** — Share integrations between OIC environments using IAR (Integration Archive) files for portable, repeatable deployments.

### Traefik Hub API Management

Traefik Hub is a Kubernetes-native API management platform built on top of Traefik Proxy, the world's most widely adopted cloud-native application proxy. Key capabilities include:

1. **Kubernetes-native CRDs** — Define APIs, plans, portals, and routing rules as Kubernetes resources, enabling GitOps workflows and infrastructure-as-code.
2. **Developer portal** — Provide a self-service portal where developers can discover APIs, view OpenAPI documentation, create applications, and subscribe to plans.
3. **API catalog and plans** — Organize APIs into catalog items with tiered plans that enforce rate limits and quotas (e.g., Gold, Silver, Bronze).
4. **JWT and SSO authentication** — Validate JWT tokens from external identity providers (including Oracle Identity Domains) and integrate OIDC-based Single Sign-On for portal access.
5. **OAuth2.0 Client Credentials middleware** — Automatically obtain backend tokens for downstream services like OIC, handling the token exchange transparently.
6. **Path rewriting and virtual endpoints** — Expose clean API paths (e.g., `/weather`) that map to complex backend URLs.
7. **Observability** — Full visibility into API traffic through the Traefik Hub dashboard, with OpenTelemetry support and integration with OCI Application Performance Monitoring and OCI Logging Analytics.

### A Note on OCI API Gateway

Oracle Cloud Infrastructure includes its own **API Gateway** service — a fully managed service for publishing APIs with private or public endpoints. OCI API Gateway provides routing, authentication, authorization, rate limiting, CORS support, and request/response transformation. It integrates natively with OCI IAM, OCI Functions (for custom authorizer logic), and other OCI services.

**When might you choose OCI API Gateway?** If your APIs are entirely within OCI, you don't need a developer portal or API catalog, and you prefer a fully managed, serverless experience with no Kubernetes dependency, OCI API Gateway is an excellent choice. It is lightweight, low-overhead, and deeply integrated with the OCI ecosystem.

**When does Traefik Hub add value?** Organizations choose Traefik Hub when their requirements include:

1. **Multi-cloud and hybrid environments** — Traefik Hub runs on any Kubernetes cluster (OKE, EKS, AKS, GKE, on-premises), providing a consistent API management experience across all environments.
2. **Full API lifecycle management** — Beyond routing and security, Traefik Hub provides a developer portal, API catalog, plans with quotas, application subscriptions, and API documentation — a complete self-service experience for API consumers.
3. **GitOps and declarative configuration** — Every Traefik Hub resource is a Kubernetes CRD, enabling version-controlled, CI/CD-driven API management without ClickOps.
4. **API mocking** — Accelerate development with mock APIs that frontend teams can consume before backend integrations are complete.
5. **Advanced routing capabilities** — Multi-layer routing, claim-based routing, canary releases, and sophisticated traffic management patterns.

Both solutions are complementary. Some organizations use OCI API Gateway for internal OCI-to-OCI routing and Traefik Hub for external-facing API management with portal and catalog capabilities.

### Oracle Kubernetes Engine (OKE)

Oracle Kubernetes Engine is a managed Kubernetes service on OCI that simplifies the deployment, management, and scaling of containerized applications. For this workshop, OKE provides the runtime environment for Traefik Hub. The OCI Marketplace includes a Terraform-based stack that provisions both the OKE cluster and the Traefik Hub deployment in a single operation, reducing setup time significantly.

## Workshop Agenda

| Lab | Title | Time |
|-----|-------|------|
| — | Introduction, Prerequisites, and Architecture Overview | 10 min |
| 1 | Deploy OKE and Traefik Hub | 25 min |
| 2 | Deploy Traefik's Sample API with Catalog and Portal | 15 min |
| 3 | Import and Configure the OIC Weather API | 15 min |
| 4 | Expose the OIC API Through Traefik Hub | 15 min |
| 5 | Secure and Test the API with JWT and SSO | 15 min |
| 6 | *(Optional)* Working with Plans, Catalog Items, and Bundles | 15 min |
| — | Clean Up Resources | 5 min |

## Pre-Workshop Validation

Before the workshop begins, confirm the following:

1. **Traefik Hub account** — Log in to [hub.traefik.io](https://hub.traefik.io) and verify you can access the dashboard. Create a new Gateway token if you haven't already.
2. **OCI access** — Log in to the OCI Console and verify you can navigate to Developer Services > Kubernetes Clusters.
3. **OIC access** — Log in to your OIC instance and verify you can access the Design > Integrations page.
4. **OpenWeather API key** — Sign in to [OpenWeather](https://home.openweathermap.org/), navigate to API Keys, and copy your key. Optionally, test it with: `https://api.openweathermap.org/?appid=YOUR_API_KEY&units=imperial`

## Learn More

* [Traefik Hub API Management — Overview](https://doc.traefik.io/traefik-hub/introduction/overview)
* [Traefik Hub — External API Integration with OCI](https://doc.traefik.io/traefik-hub/operations/oracle-oci/external-api-integration)
* [Deploy Traefik Hub API Management from Oracle OCI Marketplace](https://doc.traefik.io/traefik-hub/operations/oracle-oci/oci-apim-marketplace)
* [Traefik Labs' API Management on OCI Marketplace (Oracle Blog)](https://blogs.oracle.com/developers/traefik-labs-api-management-solution-now-available-on-oracle-cloud-marketplace)
* [Oracle + Traefik: API Management Without Boundaries](https://traefik.io/solutions/oracle-and-traefik)
* [Securing Oracle Integration Cloud APIs with Traefik on OKE (Carlos Villanua)](https://carlosvillanua.com/securing-oracle-integration-cloud-apis-with-traefik-on-oke/)
* [OCI API Gateway — Overview](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
