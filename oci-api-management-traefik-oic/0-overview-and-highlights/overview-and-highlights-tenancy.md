# Overview and Highlights

- Discuss API development and management capabilities in OIC. Outline some of the challenges.
- Discuss benefis and capabilities of Traefik Labs API Management.
- Reference architecture showing Traefik and OIC working together.

## Key Features

- Important features of OIC
- Important features of Traefik
- Brief overview of OKE

## About this Workshop

In this workshop you will learn how to build APIs with Oracle Integration Cloud (OIC), then deploy and manage those APIs with Traefik.

## Workshop Agenda (working notes)

	- (E) Introduction and overview: Recommended pre-learning for OIC, architecture diagrams, etc.
	    - Procure Traefik trial license / access to Traefik Hub
        - Validate Access to Traefik Hub
	- (E) Lab 1: Set up OKE and deploy Traefik
    - (E or V) Lab 2: Deploy Traefik's sample API (basic key auth) with catalog and portal. Test in portal.
    - (V) Lab 3: Create OIC API - Convert Docs Tutorial to Lab
	- Lab 4: Create OIDC app / OAuth config in IAM, setup SSO Auth in Traefik Hub
        - <NOTE> Wondering if we can generate API key in OCI instead of configuring JWT ???
	- Lab 6: Expose OIC API with Traefik; validate JWT / OAuth.
	- Lab 7: [Optional] Working with Plans, Catalog Items, Bundles, etc.
	- Lab 8: Clean up resources.


**Estimated Workshop Time:** 1 hour 30 minutes

## Solution Architecture

The following is a simplified solution architecture diagram for our API Management environment:

![Solution Architecture](./images/architecture.png)

As described in the diagram, our solution makes use of the following resources:

- **Oracle Kubernetes Engine (OKE)** - ...:
    - Cluster Setup
    - Storage
    - Etc.



## Objectives

In this workshop, you will learn how to:

- Create a simple API in Oracle Integration Cloud
- Deploy Traefik Hub to Oracle Kubernetes Engine (OKE)
- Integrate OCI Single Sign-On (SSO) with Traefik Hub
- Define / Deploy your OIC API to Traefik Hub
- Create and manage Bundles, Portals, Plans, and Catalog Items

## Learn More

- [Traefik Hub API Management](https://doc.traefik.io/traefik-hub/introduction/overview)
- [Traefik Labs' API Management on OCI Marketplace](https://blogs.oracle.com/developers/traefik-labs-api-management-solution-now-available-on-oracle-cloud-marketplace)
- [Deploy Traefik Hub API Management](https://doc.traefik.io/traefik-hub/operations/oracle-oci/oci-apim-marketplace)

## Acknowledgements

- **Author** - Eli Schilling & Vijaya Vishanath
- **Contributors** - 
- **Last Updated By/Date** - Published February, 2026
