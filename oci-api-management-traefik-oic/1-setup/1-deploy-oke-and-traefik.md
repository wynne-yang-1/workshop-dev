# Lab 1: Deploy OKE and Traefik Hub

## Introduction

In this lab, you will prepare your API management environment by deploying an Oracle Kubernetes Engine (OKE) cluster and installing Traefik Hub using the OCI Marketplace stack. The Marketplace stack uses Terraform to provision both the OKE cluster and the Traefik Hub Helm deployment in a single operation, significantly reducing setup time.

By the end of this lab, you will have a fully operational Traefik Hub instance running on OKE with dashboard access and a load balancer IP that you will use throughout the remaining labs.

**Estimated Time:** 25 minutes

### Objectives

In this lab you will:

1. Create a Traefik Hub Gateway token
2. Deploy the OCI Marketplace stack (OKE cluster + Traefik Hub)
3. Configure `kubectl` access to your OKE cluster
4. Verify the Traefik Hub deployment and capture your load balancer IP

### Prerequisites

This lab assumes you have:

* Completed the pre-workshop validation steps (Traefik Hub account, OCI access, Gateway token)
* Sufficient OCI privileges to create OKE clusters and deploy Marketplace stacks

## Task 1: Create Your Traefik Hub Gateway Token

Before deploying the Marketplace stack, you need a Gateway token from Traefik Hub.

1. Log in to [hub.traefik.io](https://hub.traefik.io).
2. Navigate to **Gateways** and select **Create New Gateway**.
3. Copy the generated token. You will need this in the next task.

> **Note:** If you already have a Gateway token from the prerequisites step, you can reuse it here.

## Task 2: Deploy the OCI Marketplace Stack

The Traefik Hub API Management stack on the OCI Marketplace uses Terraform to provision both the OKE cluster and the Traefik Hub Helm deployment in a single operation.

1. In the OCI Console, navigate to **Marketplace** and search for **"Traefik API Management"**.
2. Select the **Traefik Hub API Management** listing and click **Launch Stack**.
3. Review the stack information and click **Next** to proceed.
4. In the **Configure Variables** menu, provide the following:

    **Chart Configuration:**
    - **Target Namespace:** Enter `traefik`
    - **Traefik Hub Token:** Paste the Gateway token you created in Task 1

    **Helm Chart Values:**

    Add the following to the Helm values field to enable cross-namespace referencing, external API support, and the dashboard:

    ```yaml
    hub:
      token: "your-gateway-token"
    apimanagement:
      enabled: true
    ingressRoute:
      dashboard:
        enabled: true
    providers:
      kubernetesCRD:
        allowCrossNamespace: true
        allowExternalNameServices: true
    ```

    **OKE Configuration:**
    - If you **do not** have an existing OKE cluster, select the **Create Basic OKE Cluster** checkbox and provide a name for your cluster.
    - If you **do** have an existing cluster, select it from the dropdown in the **Use existing OKE** section.

    > **Note:** If using a private cluster, select the **Allow insecure connection** checkbox.

5. Click **Next**, review your configuration, and ensure the **Run apply** checkbox is checked.
6. Click **Create** to launch the stack.
7. Monitor the deployment progress on the **Stacks job page** via the logs. This process typically takes 10–15 minutes.

## Task 3: Configure kubectl Access

Once the OKE cluster is provisioned, configure your local `kubectl` to connect to it.

1. In the OCI Console, navigate to **Developer Services > Kubernetes Clusters**.
2. Select your cluster and click **Access Cluster**.
3. Follow the instructions to set up `kubectl` access (typically an `oci ce cluster create-kubeconfig` command).
4. Verify connectivity:

    ```bash
    kubectl get nodes
    ```

    You should see your cluster nodes in a `Ready` state.

## Task 4: Verify the Traefik Hub Deployment

1. Check that Traefik Hub pods are running:

    ```bash
    kubectl get pods -n traefik
    ```

    You should see the Traefik pod(s) in a `Running` state.

2. Get your Load Balancer IP address. You will use this throughout the remaining labs:

    ```bash
    export EXTERNAL_IP=$(kubectl get svc -n traefik traefik -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "Your Traefik Hub external IP: ${EXTERNAL_IP}"
    ```

    > **Important:** Save this IP address. You will need it in every subsequent lab. For production deployments, you would configure a fully qualified domain name (FQDN) pointing to this IP.

3. Verify the deployment by opening the Traefik Hub dashboard at [hub.traefik.io](https://hub.traefik.io). Your gateway should appear as connected.

## Lab 1 Recap

In this lab you deployed the foundation for the rest of the workshop:

* Created a Traefik Hub Gateway token for authenticating your OKE deployment with the Traefik Hub control plane.
* Deployed the OCI Marketplace stack, which provisioned an OKE cluster and installed Traefik Hub via Helm in a single Terraform operation.
* Configured `kubectl` access and verified that Traefik Hub pods are running.
* Captured your load balancer `EXTERNAL_IP`, which serves as the entry point for all API traffic in subsequent labs.

You may now proceed to the next lab.

## Learn More

* [Deploy Traefik Hub API Management from Oracle OCI Marketplace](https://doc.traefik.io/traefik-hub/operations/oracle-oci/oci-apim-marketplace)
* [Deploy and Configure Traefik Hub Using OCI DevOps](https://doc.traefik.io/traefik-hub/operations/oracle-oci/oci-devops)
* [Traefik Hub OCI Stacks — GitHub Repository](https://github.com/traefik/oci-traefiklabs-stacks)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
