# Clean Up: Remove Workshop Resources

## Introduction

To avoid ongoing charges and leave your environment clean, remove all resources created during this workshop. This includes the Kubernetes resources deployed to OKE, the OKE cluster itself (if created for this workshop), the OIC integration, and the Traefik Hub gateway.

**Estimated Time:** 5 minutes

### Objectives

In this lab you will:

1. Delete all Kubernetes API management resources from the `apps` namespace
2. Remove the OKE cluster and Marketplace stack (or just uninstall Traefik Hub)
3. Deactivate the OIC integration
4. Clean up the Traefik Hub gateway

### Prerequisites

This lab assumes you have:

* Completed the previous labs
* `kubectl` access to your OKE cluster

## Task 1: Delete Kubernetes Resources

Remove all the workshop resources from your OKE cluster.

1. Delete all API management CRDs and services in the `apps` namespace:

    ```bash
    # Delete API management resources
    kubectl delete apicatalogitem --all -n apps
    kubectl delete apiplan --all -n apps
    kubectl delete apiportal --all -n apps
    kubectl delete api --all -n apps
    kubectl delete ingressroute --all -n apps
    kubectl delete middleware --all -n apps
    kubectl delete secret oic-oauth2-creds -n apps
    kubectl delete service oic-backend oci-svc -n apps
    ```

2. Delete the `apps` namespace:

    ```bash
    kubectl delete namespace apps
    ```

3. Optionally, remove Redis:

    ```bash
    helm uninstall redis -n traefik
    ```

## Task 2: Delete the OKE Cluster and Marketplace Stack

**If you created the OKE cluster specifically for this workshop:**

1. In the OCI Console, navigate to **Resource Manager > Stacks**.
2. Select the Traefik Hub stack you deployed in Lab 1.
3. Click **Destroy** to tear down all Terraform-managed resources (including the OKE cluster if it was created by the stack).
4. Confirm the destruction and monitor the job logs until complete.

**If you were using an existing OKE cluster:**

1. Uninstall the Traefik Helm release and clean up the namespace instead:

    ```bash
    helm uninstall traefik -n traefik
    kubectl delete namespace traefik
    ```

## Task 3: Deactivate the OIC Integration

1. Log in to your OIC instance.
2. Navigate to your **Weather Workshop** project.
3. In the **Integrations** section, click the **Actions** menu (⋯) on the Weather By City integration and select **Deactivate**.
4. Optionally, delete the integration and project if no longer needed.

## Task 4: Clean Up Traefik Hub

1. Log in to [hub.traefik.io](https://hub.traefik.io).
2. Navigate to **Gateways** and delete the gateway you created for this workshop.

## Clean Up Recap

You have successfully removed all workshop resources:

* Deleted all **Kubernetes CRDs**, services, secrets, and the `apps` namespace.
* Destroyed the **OKE cluster and Marketplace stack** (or uninstalled Traefik Hub from an existing cluster).
* **Deactivated** the OIC Weather By City integration.
* Removed the **Traefik Hub gateway** from the online dashboard.

Thank you for completing this workshop!

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
