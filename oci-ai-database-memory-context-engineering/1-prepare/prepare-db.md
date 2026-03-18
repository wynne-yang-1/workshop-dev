# Lab 1: Prepare Development Environment

## Introduction

For the entirety of this workshop, you'll need just an Autonomous Database running Oracle AI Database 26ai and a local IDE. In this section you'll get logged into your OCI Sandbox environment, provision the DB, and set up the pre-requisites in Microsoft Visual Studio Code (installed locally on your machine).

This workshop has been tested with VS Code on both Mac and Windows. If you prefer to use a different IDE, some of the instructions in this section may vary slightly.

**Estimated Time:** 15 minutes

### Objectives

In this lab, you will:

1. Log into the provided OCI tenancy
2. Use Coud Shell / CLI to provisiong the Autonomous Database (ADB)
3. Connect to the ADB instance and create a dedicated user for vector operations

### Prerequisites

This lab assumes you have:

- Provisioned the Workshop using the LiveLabs Sandbox
- Retrieved your account credentials from the LiveLabs UI
- Have Microsoft VS Code installed on your computer

## Task 1: Log into the OCI Tenancy

1. Click the **View Loging Info** link to access account information.

    ![LiveLabs - Account Info Link](images/02-view-login-info.png " ")

2. Locate and copy the Compartment OCID value. Store it in a text file to use in just a minute.

3. Click the **[Launch OCI]** button and log in with the *Username* and *Password* provided.

    ![LiveLabs - Log into OCI](images/02-launch-oci.png " ")

4. You should land on the OCI Dashboard, at which point you can proceed to the next task.

## Task 2: Create an Autonomous Database Instance

1. Open Cloud Shell

    ![Cloud shell button in UI](images/02-cloud-shell-button.png " ")

2. Copy the following command. Replace `<your-compartment-ocid>` with the value copied earlier.

    ```bash
    <copy>
    oci db autonomous-database create \
    --compartment-id "<your-compartment-ocid>" \
    --db-name "memengdb" \
    --admin-password 'WElcome123##' \
    --compute-model ECPU \
    --compute-count 4 \
    --data-storage-size-in-tbs 1 \
    --display-name 'MemoryEngineering' \
    --is-free-tier false \
    --license-model LICENSE_INCLUDED \
    --db-workload DW \
    --db-version 26ai
    </copy>
    ```

    >NOTE: You're welcome to choose your own `admin-password` and/or `disply-name` if you'd like.

3. The command will return a large block of JSON:

    Starting with:
    ```
    {
    "data": {
        "actual-used-data-storage-size-in-tbs": null,
        "additional-attributes": null,
        "allocated-storage-size-in-tbs": null,
        "apex-details": null,
        "are-primary-whitelisted-ips-used": null,
        "auto-refresh-frequency-in-seconds": null,
    ```

    ...and ending with:
    ```
        "vanity-connection-urls": null,
        "vanity-url-details": {
        "api-gateway-id": null,
        "is-disabled": true,
        "vanity-url-host-name": null
        },
        "vault-id": null,
        "whitelisted-ips": null
    },
    "etag": "bffaf316--gzip",
    "opc-work-request-id": "ocid1.coreservicesworkrequest.oc1.phx.abyh.......ykzp2ltfr7kqa"
    }
    ```

4. Use the navigation menu to visit the Autonous AI Database service console.

    ![Web UI Nav Menu showing Oracle AI Database](images/02-nav-adb.png " ")

5. Once the *State* of the database is `Avaialble`, click the name of the DB instance.

    ![ADB Service Console showing DB instance](images/02-adb-service-console.png " ")

6. Scroll down the page and locate the **Network** section.

    ![ADB Instance details - Network section](images/02-adb-details-network.png " ")

7. Click the **[Edit]** button next to **`Access control list`**.

8. Click the *Add my IP address(shows your IP here) to IP value* toggle switch. You should notice the Values field above will populate with the external IP of your current machine.

    ![Network ACL - Add my IP](images/02-adb-network-acl.png " ")

9. Click **[Save]** and allow the database a minute or so to update. Once the **[Edit]** button next to *Mutual TLS (mTLS) authentication is no longer grayed out, you may proceed to the next step.

10. Click said **[Edit]** button next to the mTLS setting. Click the toggle switch to not require MTLs auth. Click **[Save]**.

    ![Edit MTLS settings dialog](images/02-adb-network-mtls.png " ")
 
11. Finally - scroll back to the top of the page and click the **[Database connection]** button. Locate and copy the full **Connection string** for the TNS name that corresponds with `medium`. (Paste in a note pad for future reference)

    ![Database connection details screen](images/02-adb-connection-details.png " ")

12. Time to set up VS Code!!

## Task 3: Open VS Code and Create Jupyter environment

For this lab, you will create a new `.ipynb` file and copy in the code to prep the database. The remainder of the labs key off a single, consolidated notebook that will ensure a consistent flow throughout.

<details><summary>IDE Setup in Windows</summary>

1. Ensure that you have **`Python 3.11.9`** or newer installed.

    * Use the Python installer to get the latest version: [Download Python Installer for Windows](https://www.python.org/downloads/release/pymanager-260/)

    * Use `pyenv-win` to install and manage multiple versions of Python.

        * Open **PowerShell as an Administrator** 
        * Run `Get-ExecutionPolicy` - if it is anything other than *Unrestricted* or *RemoteSigned*, you'll need to run `Set-ExecutionPolicy RemoteSigned`
        * Install `pyenv-win` with this command:
            ```bash
            <copy>
            Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
            </copy>
            ```
        * Install the latest version of v3.12: `pyenv install 3.12.10`

            ![Using pyenv-win to install Python 3.12.10](images/02-win-pyenv-install.png " ")

2. Open VS Code and close any existing tabs. 

2. Create a new Workspace: **File** -> **Open Folder**

3. Select an existing folder where you'd like to create your workspace, or create and select a new folder.

    ![Select workspace folder dialog window](images/02-vscode-select-workspace.png " ")

    >NOTE: If prompted to trust the authors of the files in this folder, click **[Yes, I trust the authors]**

6. Press `Ctrl+Shift+P` and begin typing "Jupyter". It should auto-populate the option to `Create: New Jupyter Notebook`. Select this option.

7. A new, `Untitled-1.ipynb` file will be created. For the best experience, you'll want to create a virtual environment fo the workshop. Click **[Select Kernel]** in the top right corner of VS Code.

8. Click *+ Create Python Environment*

    ![Menu option to create python evironment](images/02-vscode-select-kernel.png " ")

9. Choose the ***venv** Manages virtual environments created using 'venv'* 

10. Select desired Python version and assign a name: `oracle-agent-env`

    >NOTE: For creating / testing the workshop I used 3.12.10 on Windows

11. You can skip package installation. We'll do that in a separate step. 

12. VS Code will automatically install a bunch of required packages to support Jupyter notebooks. We'll go ahead and add a few more that are required for the workshop. Paste the following and run the code block:

    ```
    <copy>
    pip install -qU oracledb langchain-oracledb langchain langchain-openai langchain-huggingface ipywidgets tavily-python sentence-transformers ipykernel jupyter numpy datasets
    </copy>
    ```

    >NOTE: This will perform a quiet install that takes 3-5 minutes. No output will be diplayed until it completes.

13. Test to make sure the Python modules were installed properly. Create a new code block, then paste and run the following:

    ```
    from openai import OpenAI
    from langchain_huggingface import HuggingFaceEmbeddings
    import oracledb
    ```

    >NOTE: No output is displayed unless there are errors. If you see a green check mark, all is well!

14. Finally, before continuing to the next step, restart the kernel.

    ![Restart kernel button in VS Code](images/02-vscode-restart-kernel.png " ")

</details>

<details><summary>IDE Setup for MacOS</summary>

1. First off, make sure you have the necessary tools installed.

    * **Conda:** Install via [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended) or [Anaconda](https://www.anaconda.com/download)
    * **pyenv:** Install via [pyenv GitHub](https://github.com/pyenv/pyenv) OR `brew install pyenv`. Get Homebrew at [brew.sh](https://brew.sh/)
    * **VS Code:** Download at [code.visualstudio.com](https://code.visualstudio.com/)

2. Next - decide whether you want to use **Conda** or **pyenv + venv** for your development environment. Execute one of the following in your shell.

    * Option A: Conda:

        ```bash
        <copy>
        conda create -n oracle-agent-env python3.11
        conda activate oracle-agent-env
        </copy>
        ```

        ![Shell command to create and activate conda environment](images/02-mac-create-conda.png " ")

    * Option B: pyenv + venv

        ```bash
        <copy>
        pyenv install 3.11.9    # skip if already installed
        pyenv local 3.11.9
        python -m venv oracle-agent-env
        source oracle-agent-env/bin/activate
        </copy>
        ``` 
    
    >NOTE: Once activated, your terminal prompt shows *(oracle-agentenv)*. Keep this session open for the duration of the workshop.

3. Open VS Code and create a new Workspace: **File -> Open Folder**

4. Select an existing folder or create and select a new one.

    ![VS Code Open Folder](images/02-mac-open-folder.png " ")

    >NOTE: If prompted to trust the authors of the files in this folder, click **[Yes, I trust the authors]**

5. Press *Cmd+Shift+P* and begin typing "*Jupyter*". Select *Create: New Jupyter Notebook*

    ![Create new jupyter notebook](images/02-mac-create-jupyter-notebook.png " ")

    >NOTE: You may need the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) if not already installed.

6. A new *Untitled-1.ipyn* file will be created. Confirm the kernel in the top right corner matches your environment.

    ![Validate selected kernel](images/02-mac-validate-kernel.png " ")

7. Paste the following code in the initial code block and press play.

    ```bash
    <copy>
    pip install -qU oracledb langchain-oracledb langchain langchain-openai langchain-huggingface ipywidgets tavily-python sentence-transformers ipykernel jupyter numpy datasets
    </copy>
    ```

    >NOTE: This will perform a quiet install that may take 3-5 minutes. No output will be displayed until it completes.

8. Test the installation by creating a new code block, then paste and run:

    ```bash
    <copy>
    from openai import OpenAI
    from langchain_huggingface import HuggingFaceEmbeddings
    import oracledb
    </copy>
    ```

    ![Output of test python code](images/02-mac-verify-setup.png " ")

    >NOTE: Check for the green check mark and *All modules imported uccessfully - no errors*

9. Finally, restart the kernel before proceeding to the next section.

</details>

## Task 4: Connect to the database and create VECTOR user

1. Now test the connection using the OracleDB driver for Python. When you run this code block, VS Code will prompt you for three values. After entering these three values, the code block will finish executing.

    * Your autonomous database admin password
    * Your chosen VECTOR user password (recommended: MemoryContext_2026)
    * The DSN for your Autonomous DB _medium listener

    ![VS Code prompt for input - DB Admin password](images/02-vscode-run-code-prompt.png " ")

    ```python
    <copy>

    import oracledb
    import os
    import getpass

    # Store username, password, and DSN
    adb_password = getpass.getpass("Database password: ")
    vector_password = getpass.getpass("Enter password for VECTOR (e.g. MemoryContext_2026): ")
    adb_dsn = os.environ.get("DB_DSN", input("Database DSN copied earlier: "))
    adb_user = "ADMIN"
    vector_user = "VECTOR"

    %store adb_dsn vector_user vector_password
    try:
        connection = oracledb.connect(
            user=adb_user,
            password=adb_password,
            dsn=adb_dsn
        )

        print("Connection Successful")

        with connection.cursor() as cursor:
            cursor.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
            banner = cursor.fetchone()[0]
            print(f"\n{banner}")
            
    except oracledb.Error as error:
        print(f"Error connecting to the database: {error}")

    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("Connection Closed.")
    </copy>
    ```

    ![Successful DB connection output in VS Code](images/02-vscode-db-connection-success.png " ")

3. Create the VECTOR user.

    ```python
    <copy>

    def setup_oracle_adb(
        create_vector_user=True,
        vector_user=vector_user,
        vector_password=vector_password 
    ) -> bool:
        """
        Connect to Oracle Autonomous Database and create VECTOR user
        
        Args:
            create_vector_user: Whether to create a VECTOR user
            vector_user: Username for the vector user
            vector_password: Password for the vector user
        
        Returns:
            bool: True if setup succeeded, False otherwise
        """
        print("=" * 60)
        print("🚀 ORACLE AUTONOMOUS DATABASE SETUP")
        print("=" * 60)
        
        # Step 1: Install/verify oracledb
        print("\n[1/3] Checking oracledb driver...")
        try:
            import oracledb
            print(f"   ✅ oracledb version {oracledb.__version__} installed")
        except ImportError:
            print("   ❌ oracledb not installed!")
            print("   💡 Install with: pip install oracledb")
            return False
        
        # Step 2: Test connection with wallet
        print("\n[2/3] Testing connection to Autonomous Database...")
        
        try:
            # Configure wallet location for thin mode
            connection = oracledb.connect(
                user=adb_user,
                password=adb_password,
                dsn=adb_dsn
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
                version = cursor.fetchone()[0]
                print(f"   ✅ Connected successfully!")
                print(f"   📊 {version}")
            
        except oracledb.Error as e:
            error = e.args[0]
            print(f"   ❌ Connection failed: {error.message}")
            
            # Provide helpful hints based on error code
            if "ORA-01017" in str(error):
                print("   💡 Invalid username/password. Check your credentials.")
            elif "ORA-12154" in str(error):
                print("   💡 TNS could not resolve service name. Check tns_alias parameter.")
            elif "ORA-28759" in str(error):
                print("   💡 Failed to open wallet. Check wallet_password.")
            elif "ORA-28858" in str(error):
                print("   💡 Wallet file error. Re-download the wallet from OCI.")
            
            return False
        
        # Step 3: Create VECTOR user (optional)
        if create_vector_user:
            print(f"\n[3/3] Creating {vector_user} user...")
            
            try:
                with connection.cursor() as cursor:
                    # Check if user exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM all_users WHERE username = :1",
                        [vector_user.upper()]
                    )
                    user_exists = cursor.fetchone()[0] > 0
                    
                    if user_exists:
                        print(f"   ✅ {vector_user} user already exists")
                    else:
                        # Create user with appropriate privileges
                        cursor.execute(f'CREATE USER {vector_user} IDENTIFIED BY "{vector_password}"')
                        cursor.execute(f"GRANT CONNECT, RESOURCE TO {vector_user}")
                        cursor.execute(f"GRANT UNLIMITED TABLESPACE TO {vector_user}")
                        cursor.execute(f"GRANT CREATE TABLE, CREATE SEQUENCE, CREATE VIEW TO {vector_user}")
                        
                        # For vector operations in ADB
                        try:
                            cursor.execute(f"GRANT EXECUTE ON DBMS_VECTOR TO {vector_user}")
                            cursor.execute(f"GRANT EXECUTE ON DBMS_VECTOR_CHAIN TO {vector_user}")
                        except oracledb.Error:
                            # These grants may not be available in all ADB versions
                            pass
                        
                        connection.commit()
                        print(f"   ✅ {vector_user} user created successfully")
                        
            except oracledb.Error as e:
                print(f"   ⚠️  Could not create user: {e.args[0].message}")
                print("   💡 You may need DBA privileges to create users.")
        else:
            print("\n[3/3] Skipping user creation (create_vector_user=False)")
        
        connection.close()
        
        # Success summary
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        print(f"""
    Connection Details:
        Service: {adb_dsn}
        Admin User: {adb_user}
    """)
        
        if create_vector_user:
            print(f"""    
    Vector User Credentials:
        User: {vector_user}
        Password: {vector_password}
    """)

        return True

    setup_oracle_adb()
    <copy>
    ```

    ![Notebook execution output - successfully created vector user](images/02-vscode-dbsetup-output.png " ")

You may now proceed to the next lab.

## Learn More



## Acknowledgements

- **Author** - Richmond Alake
- **Contributors** - Eli Schilling
- **Last Updated By/Date** - Published February, 2026