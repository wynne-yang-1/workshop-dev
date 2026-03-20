# Lab 1: Data Environment Setup

## Introduction

Before building the AI agent, we need to ensure the data environment is in place. In this lab, you'll explore the pre-configured catalog and volume that have been set up for the workshop, then create a Knowledge Base that turns those documents into vector representations for RAG retrieval. You'll also verify the Oracle AI Database tables that will power the agent's SQL tools.

By the end of this lab, all the data assets — structured (database tables) and unstructured (knowledge base documents) — will be ready for the agent flow you'll build in Lab 2.

**Estimated Time:** 15 Minutes

### Objectives

In this lab you will:

1. Explore the pre-configured standard catalog (`agent_assets`) and managed volume (`entertainment_analyst`) containing release playbooks and strategy documents
2. Create a Knowledge Base and populate it with the documents from the volume
3. Verify the Oracle AI Database tables that contain box office, streaming, and marketing data
4. Understand how the structured (SQL) and unstructured (RAG) data assets connect to the agent you'll build

### Prerequisites

This lab assumes you have:

* Reviewed the Workshop Introduction and Overview
* Access to the AIDP Workbench instance provisioned for this workshop
* The following resources have been pre-configured by your facilitator:
    * A standard catalog named `agent_assets`
    * A managed volume named `entertainment_analyst` with release playbooks and strategy documents already uploaded
    * An Oracle AI Database with entertainment performance tables already ingested

## Task 1: Explore the Standard Catalog

A standard catalog in AIDP stores AI-related artifacts — volumes, tables, schemas, and knowledge bases. For this workshop, a catalog has been pre-created to hold all the assets our agent will need.

1. From the AIDP Workbench Home Page, click on **Master Catalog**.

2. Locate the catalog named **`agent_assets`**. Click on it to open it.

3. Take a moment to review the catalog. Notice that it is a **Standard Catalog** — meaning it stores data directly within AIDP (backed by OCI Object Storage and Delta Lake), as opposed to an External Catalog which connects to data outside the platform.

4. Click on the **default** schema within the catalog. This is where the volume and knowledge base assets are organized.

    > **Note**: This catalog was pre-created for the workshop to save time. In a real-world scenario, you would create this catalog yourself by clicking **Create Catalog** from the Master Catalog page, giving it a name and description, selecting "Standard Catalog" as the type, and leaving the compartment field blank.

## Task 2: Explore the Managed Volume

A volume stores unstructured data — files, documents, images — within a catalog. The volume for this workshop contains the internal release playbooks and strategy documents that the RAG tool will search.

1. Inside the **`agent_assets`** catalog, click on the **default** schema, then click on **Volumes**.

2. Locate the volume named **`entertainment_analyst`**. Click on it.

3. Review the files that have been uploaded. You should see the following internal documents:

    - **Content Strategy & Release Operations Playbook** — Defines release windows, territory prioritization, green/yellow/red performance signals, and decision frameworks
    - **Marketing Measurement & Attribution Guidelines** — Defines metric definitions (e.g., completion rate, ROI), attribution logic, and interpretation rules
    - **Distribution Window & Territory Rules** — Defines territorial constraints, windowing strategies, and market codes

4. These are the documents that the AI agent will search via RAG when users ask questions about definitions, policies, thresholds, or interpretation rules. For example, when a user asks *"What does our playbook say about territory priorities for releases?"*, the agent will retrieve relevant passages from these documents.

    > **Note**: This volume was pre-created and pre-populated for the workshop. In a real-world scenario, you would create the volume by navigating to the default schema, clicking **Volumes**, clicking the **+** button, selecting "Managed" volume, and then uploading your files via drag-and-drop.

## Task 3: Create a Knowledge Base

Now we'll create the key asset that enables RAG. A Knowledge Base creates vector representations (embeddings) of the documents in the volume. When the agent receives a question, it performs a semantic search against these vectors to find the most relevant passages — even if the user's wording doesn't exactly match the document text.

1. Navigate back to the **`agent_assets`** catalog. Click on the **default** schema.

2. Click on **Knowledge Bases**.

3. Click the **+** button to create a new Knowledge Base.

4. Enter the following values:

    ```
    Name: entertainment_analyst_kb
    Description: Contains internal release playbooks, marketing guidelines, and distribution rules
    ```

5. Leave the **Advanced Settings** as-is for now. These settings control the embedding model, chunk size, and chunk overlap. The defaults are appropriate for this workshop.

6. Click **Create**. The Knowledge Base will take a few seconds to become Active.

7. Once the Knowledge Base shows status **Active**, click on it to open the details.

8. Under the **Data Source** tab, click the **+** button to add a data source.

9. In the data source selection window, select the **`entertainment_analyst`** volume from your catalog. This is the volume containing the release strategy and playbook documents. Leave all advanced settings as-is.

10. Click **Add**.

11. Navigate to the **History** tab of your Knowledge Base. You should see a line entry with the operation name **"Update Knowledge Base"**. This step ingests the documents — chunking them, generating embeddings, and indexing the vectors.

12. Wait for the status to show **Succeeded** before moving on. This typically takes less than one minute since we're ingesting a small set of documents.

    > **What just happened?** The Knowledge Base chunked each document into smaller passages, generated vector embeddings for each chunk using an embedding model, and stored those vectors in an index. When the RAG tool receives a query, it converts the query into a vector, finds the most semantically similar chunks, and returns them as context for the LLM. This is how the agent can answer policy and definition questions grounded in your actual internal documents.

## Task 4: Verify the Oracle AI Database Tables

The agent's SQL tools query structured data from an Oracle AI Database. For this workshop, the following tables have been pre-ingested with entertainment performance data.

1. Your facilitator will provide connection details for the Oracle AI Database. The tables are stored in the `entertainment` schema (or the schema specified by your facilitator).

2. Verify that the following tables exist and contain data:

    | Table Name | Description | Key Columns |
    |---|---|---|
    | `titles` | Master list of all movies and TV shows | `title_id`, `title_name` |
    | `markets` | Reference table of market codes, names, and currencies | `market_code`, `market_name`, `currency` |
    | `box_office_weekend` | Weekend theatrical performance by title and market | `title_id`, `weekend_end_date`, `market_code`, `gross_usd_m`, `screens`, `rank` |
    | `streaming_weekly` | Weekly streaming metrics by title and region | `title_id`, `week_start_date`, `region_code`, `starts`, `hours_streamed_k`, `completion_rate` |
    | `marketing_campaigns` | Campaign metadata linking campaigns to titles | `campaign_id`, `campaign_name`, `title_id`, `start_date`, `end_date` |
    | `marketing_daily_spend` | Daily spend and attributed revenue by campaign and channel | `campaign_id`, `channel`, `spend_usd`, `attributed_revenue_usd` |

3. These tables represent the **gold layer** of the medallion architecture — curated, query-optimized data ready for business consumption. The agent's SQL tools will execute parameterized, read-only queries against these tables to answer performance and ROI questions.

    > **Key takeaway**: You now have two categories of data assets ready for the agent:
    > - **Unstructured (RAG)**: The Knowledge Base with vector-indexed release playbooks and strategy documents — for answering questions about definitions, policies, and interpretation rules
    > - **Structured (SQL)**: The Oracle AI Database tables with box office, streaming, and marketing data — for answering questions about specific metrics, trends, and ROI numbers

## Lab 1 Recap

In this lab, you set up the complete data environment for the Entertainment Analyst agent:

- You explored the pre-configured **`agent_assets`** standard catalog and the **`entertainment_analyst`** volume containing internal release playbooks and strategy documents.
- You created a **Knowledge Base** (`entertainment_analyst_kb`), populated it with documents from the volume, and verified that the ingestion succeeded. This enables RAG — the agent can now search your internal documents by semantic meaning.
- You verified the **Oracle AI Database tables** containing box office, streaming, and marketing campaign data. These power the agent's SQL tools.

In the next lab, you'll create the agent flow itself — configuring the AI Compute, building the agent node, and wiring up the RAG and SQL tools.

## Learn More

* [Unlock the Power of the Catalog in AIDP Workbench — Oracle Community](https://community.oracle.com/products/oracleaidp/discussion/27748/unlock-the-power-of-the-catalog-in-aidp-workbench)
* [AIDP Workbench FAQs: Collaboration, Medallion Architecture, and Data Storage — Oracle Community](https://community.oracle.com/products/oracleanalytics/discussion/28251/aidp-workbench-faqs-collaboration-medallion-architecture-and-data-storage)
* [Oracle AI Data Platform — Documentation](https://docs.oracle.com/en/cloud/paas/ai-data-platform/)
* [Oracle AI Data Platform — Sample Notebooks on GitHub](https://github.com/oracle-samples/oracle-aidp-samples)

## Acknowledgements

* **Author(s)** - Jean-Rene Gauthier [AIDP]
* **Contributors** - Eli Schilling - Cloud Architect, Gareth Nathan - SDE, GenAI
* **Last Updated By/Date** - Published March 2026
