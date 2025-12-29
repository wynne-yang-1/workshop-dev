# Lab 3: Create the Agent

## Introduction

In this lab we are going to create the intelligent agent which will drive our entire solution. We will provide the agent with the required tools and knowledge bases to perform it's work effectively. Tools are resources the agent can use to perform it's tasks. In our use-case, we are going to use two tools:

- **RAG Tool** - Which will scan the grid policy documents uploaded to object storage whenever the user requires such information.
- **SQL Tool** - Which will be able to retrieve information stored in our database instance relating to the interconnection request system.

**Estimated Time:** 15 minutes

### Objectives

In this lab, you will:

- Create our agent including the RAG & SQL Tools and assign the relevant knowledge base to each.

### Prerequisites

This lab assumes you have:

- All previous labs successfully completed.

## Task 1: Create the agent

1. In the OCI Console, click the **Region** selector in the top-right corner and switch to **US Midwest (Chicago)** for this workshop.

    ![Screenshow showing list of regions](./images/region-selector.png)

2. Click the navigation menu on the top left.

3. Click **Analytics & AI**.

4. Click **Generative AI Agents**.

    ![Screenshot showing navigation to AI Agents](./images/nav-ai-agents.png)

5. In the overview page, click the **Agents** link.

6. Under the **List scope** section, make sure that your compartment is selected.

7. Click the **Create Agent** button at the top of the Agents table.

    ![Screenshot showing create agent](./images/create-agent.png)

8. For the **Name** field use: `grid operations agent`

9. For the **Compartment** field, make sure that your compartment is selected.

10. For the **Description** field, use: `This agent assists Directors of Grid Operations in reviewing solar PV interconnection requests, evaluating grid compliance, and providing approval recommendations.`

11. For the **Welcome message** field, use: `Hello! I'm your Grid Operations Assistant. I can help you review interconnection requests, check compliance with grid standards, and answer questions about our policies. How can I assist you today?`

12. Click the **Next** button.

    ![Screenshot showing agent basic info](./images/agent-basic-info.png)

## Task 2: Add the RAG Tool

1. Under the **Tools** section, click the **Add tool** button to create our first tool.

    ![Screenshot showing add tool](./images/add-tool.png)

2. Select the **RAG tool** option.

3. Under the RAG Configuration section, use `Grid Policy Knowledge Base` in the **Name** field.

4. For the **Description** field, use: `Use this tool when users ask about policies, standards, compliance requirements, or approval/denial criteria. Retrieves grid interconnection policies including: IEEE 1547 voltage/frequency requirements, UL 1741 inverter certification, anti-islanding protection rules, ride-through guidelines, regional grid capacity limits, California Rule 21, safety/installation standards, and net metering policies.`

    It is very important to provide a high-level description of the knowledge that this tool can retrieve. This allows the agent to make accurate decisions when choosing to invoke this tool.

    ![Screenshot showing RAG tool config](./images/rag-tool-config.png)

5. Under the **Add knowledge bases** section, make sure that your compartment is selected in the **Compartment** field.

6. Click the **Create knowledge base** button. In this step we are going to create a knowledge base which references the storage bucket into which we've uploaded the grid policy documents.

    ![Screenshot showing create KB](./images/create-kb.png)

7. In the New knowledge base form, use: `Grid Operations Knowledge Base Policy Documents` for the **Name** field.

8. Make sure that your compartment is selected in the **Compartment** field.

9. In the **Data store type** field, we will select **Object storage** to be able to retrieve information from our storage bucket.

10. Make sure that **Enable hybrid search** is checked. Enabling this option instructs the system to combine lexical and semantic search when scanning our documents.

11. Click the **Specify data source** button.

    ![Screenshot showing KB form](./images/kb-form.png)

12. In the Specify data source form, use: `grid policy docs` for the **Name** field.

13. Make sure that the **Enable multi-modal parsing** option is not checked. This option enable parsing of rich content, such as charts and graphics, to allow responses based on visual elements. However, we do not have any images in our policy documents so right now this option is not required.

14. Under the **Data bucket** option, select the **grid-policy-documents** bucket into which we've previously uploaded the grid policy PDF files.

15. Check the **Select all in bucket** option. This option will automatically flag all of the file in the bucket for ingestion instead of us having to select each file individually.

16. Click the **Create** button.

    ![Screenshot showing data source form](./images/data-source-form.png)

17. Back in the New knowledge base panel, the `grid policy docs` data source was added to the Data source table.

18. Make sure that the **Automatically start ingestion job for above data sources** option is checked. This will create an ingestion job which will scan all of our files automatically when the knowledge base is initially created. Please note that this will only run the ingestion job once. In order to re-ingest information from the bucket in the future, you will need to trigger a job manually.

19. Click the **Create** button.

    ![Screenshot showing KB create](./images/kb-create.png)

20. The knowledge base will take a few minutes to create and ingest the data. You may proceed to the next step while the knowledge base provisions.

21. Back at the Add knowledge bases panel, make sure that the checkbox next to the knowledge base name is checked.

> 💡 If your knowledge base does not appear ("No items found"), you can still continue to the next step. The knowledge base is already selected and provisioning in the background. You may open a new tab and navigate to Agents > Knowledge Bases to confirm it is provisioning.

22. Click the **Add tool** button.

    ![Screenshot showing add RAG tool](./images/add-rag-tool.png)

## Task 3: Add the SQL Tool

1. Now that we have our RAG tool configured, let's configure our SQL tool. In the Tools section Click the **Add tool** button.

    ![Screenshot showing add SQL tool button](./images/add-sql-tool-button.png)

2. Click the **SQL** option.

3. For the **Name** field, use: `Interconnection Request Database`.

4. For the **Description** field, use: `Use this tool when users ask about interconnection requests, PV systems, grid operators, workload, assignments, or application status. Contains database tables for: PV system specifications (capacity, inverter details, certification status), interconnection requests (application ID, requested capacity, voltage level, grid impact score, compliance status, local grid capacity), grid operators (name, region, assignments), and request statuses (Pending Review, Technical Review, Approved, Denied).`

    ![Screenshot showing SQL tool config](./images/sql-tool-config.png)

5. Under **Import database schema configuration for this tool**, select the **Inline** option which will allow us to use the same schema text we've used when we created the database.

6. Copy the following text and paste it into the **Database schema** field:

    ```sql
    CREATE TABLE PV_Systems (
      SystemID             NUMBER PRIMARY KEY,
      ExternalSystemID     VARCHAR2(20) UNIQUE,
      InstallerName        VARCHAR2(100) NOT NULL,
      SiteAddress          VARCHAR2(200),
      City                 VARCHAR2(50),
      State                VARCHAR2(2),
      ZipCode              VARCHAR2(10),
      SystemCapacityKW     NUMBER,
      InverterManufacturer VARCHAR2(100),
      InverterModel        VARCHAR2(100),
      InverterCertification VARCHAR2(50)
    );

    CREATE TABLE Grid_Operators (
      OperatorID NUMBER PRIMARY KEY,
      FirstName  VARCHAR2(50) NOT NULL,
      LastName   VARCHAR2(50) NOT NULL,
      Email      VARCHAR2(100) UNIQUE NOT NULL,
      Phone      VARCHAR2(20),
      Region     VARCHAR2(50)
    );

    CREATE TABLE Request_Status (
      StatusID   NUMBER PRIMARY KEY,
      StatusName VARCHAR2(50) NOT NULL
    );

    CREATE TABLE Interconnection_Requests (
      RequestID           NUMBER PRIMARY KEY,
      ApplicationID       NUMBER UNIQUE NOT NULL,
      SystemID            NUMBER NOT NULL,
      RequestType         VARCHAR2(50) NOT NULL,
      RequestedCapacityKW NUMBER NOT NULL,
      VoltageLevel        VARCHAR2(20),
      GridImpactScore     NUMBER,
      SubmittedDate       DATE NOT NULL,
      LastUpdatedDate     DATE NOT NULL,
      StatusID            NUMBER NOT NULL,
      AssignedOperatorID  NUMBER,
      InverterCompliant   VARCHAR2(3),
      LocalGridCapacityMW NUMBER
    );
    ```

7. Under the **In-context learning examples**, leave the **None** option selected.

8. Under the **Description of tables and columns**, select the **Inline** option.

9. Copy and paste the following text into the **Description of tables and columns**. This verbal description contains details about each table and column. This will allow the tool to better understand the data stored in our database:

    ```
    PV_Systems — Photovoltaic system specifications and equipment details.
      SystemID (number): PK
      ExternalSystemID (string): Business ID (e.g., PV_22000)
      InstallerName: Solar installation company
      City, State, ZipCode: System location
      SystemCapacityKW (number): PV system size in kilowatts
      InverterManufacturer, InverterModel: Equipment details
      InverterCertification (string): UL1741, IEEE1547, or None

    Grid_Operators — Grid operations staff directory.
      OperatorID (number): PK
      FirstName, LastName, Email, Phone
      Region (string): Geographic area of responsibility (e.g., Southwest, California, Midwest)

    Request_Status — Interconnection request lifecycle statuses.
      StatusID (number): PK
      StatusName (string): one of Pending Review, Technical Review, Approved, Denied

    Interconnection_Requests — Solar PV grid interconnection applications.
      RequestID (number): PK
      ApplicationID (number): External application ID (unique)
      SystemID (number): FK → PV_Systems.SystemID
      RequestType (string): New, Upgrade, Modification
      RequestedCapacityKW (number): Requested connection capacity in kilowatts
      VoltageLevel (string): 240V, 480V, 12kV, 69kV, etc.
      GridImpactScore (number): Impact assessment score (0-100, higher means more impact)
      SubmittedDate (date), LastUpdatedDate (date)
      StatusID (number): FK → Request_Status.StatusID
      AssignedOperatorID (number): FK → Grid_Operators.OperatorID
      InverterCompliant (string): 'Yes'/'No' - meets UL1741/IEEE1547 certification
      LocalGridCapacityMW (number): Available local grid capacity in megawatts
    ```

    ![Screenshot showing SQL schema config](./images/sql-schema-config.png)

10. For **Model customization**, select the **Small** option.

11. For **Dialect**, select **Oracle SQL**.

12. In the **Database tool connection**, select your compartment, then choose the `connection-gridinterconnectXXXX` connection we previously created.

> 💡 If your database tool connection does not appear in your compartment ("Option not available"), select Cancel and re-add the SQL tool by repeating Task 3: Add the SQL Tool.

13. Click the **Test connection** button. You should see a successful connection connection attempt.

14. Enable the **SQL execution** option. This option will instruct the tool to execute the SQL queries generated by the tool as a result of the user's requests. This will allow the agent to craft intelligent responses based on the data returned from the queries.

15. Enable the **Self correction** option. Enabling this option will allow the tool to automatically detect and correct syntax errors in generated SQL queries.

16. Click the **Add tool** button.

    ![Screenshot showing SQL tool complete](./images/sql-tool-complete.png)

17. Back in the Tools section, Click **Next**.

    ![Screenshot showing tools complete](./images/tools-complete.png)

## Task 4: Setup the Agent Endpoint

1. In the **Setup agent endpoint** section, check the **Automatically create an endpoint for this agent**.

2. Enable the **Enable human in the loop** option. This will enable the agent to ask for additional human input or information if needed.

    ![Screenshot showing endpoint config](./images/endpoint-config.png)

3. We are going to leave all of the options under **Guardrails** for Content moderation, Prompt injection (PI) protection & Personally identifiable information (PII) protection sections as **Disabled**. Those options are important but not required for our demonstration. Please refer to the Learn More section below for additional information about those options.

4. Click the **Next** button.

    ![Screenshot showing guardrails](./images/guardrails.png)

## Task 5: Review and Create

1. In the **Review and create** page, review the agent information and click the **Create agent** button.

    ![Screenshot showing review and create](./images/review-create.png)

2. In the license agreement dialog, review the agreement, check the consent checkbox and click the **Submit** button.

    ![Screenshot showing license agreement](./images/license-agreement.png)

3. The agent will take a few minutes to create. When complete, the agent's **Lifecycle state** will show **Active**.

    ![Screenshot showing agent active](./images/agent-active.png)

You may now proceed to the next lab.

## Learn More

- [Creating an Agent in Generative AI Agents](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/create-agent.htm)
- [Add AI Guardrails to OCI Generative AI Model Endpoints](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/guardrails.htm)

## Acknowledgements

- **Author** - Deion Locklear
- **Contributors** - Hanna Rakhsha, Daniel Hart, Uma Kumar, Anthony Marino
