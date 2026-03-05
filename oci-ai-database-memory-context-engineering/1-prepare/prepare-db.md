# Lab 1: Prepare Development Environment

## Introduction

As part of the Sandbox environment, an Autonomous Database running Oracle AI Database 26ai has already been provisioned for you. We'll be doing all of the workshop activities inside the Oracle Machine Learning (OML) notebook environment. In this section you'll get acclimated with the Autonomous database instance and the OML environment, then create a VECTOR user for use in the subsequent labs.

**Estimated Time:** 0 minutes

### Objectives

In this lab, you will:

1. Log into the provided OCI tenancy
2. Review the Autonomous Database that was provisioned for you
3. Create a dedicated user for vector operations

### Prerequisites

This lab assumes you have:

- Provisioned the Workshop using the LiveLabs Sandbox
- Retrieved your account credentials from the LiveLabs UI

## Task 1: Log into the OCI Tenancy

...

## Task 2: Locate and review the Oracle AI Database 26ai instance

1. From the Database Connection screen, copy the full connection string for the TNS name that corresponds with `medium`. (Paste in a note pad for future reference)



## Task 3: Open the OML Workbench

1. From the Database instance screen, click **[Database actions]** and select **View all database actions**.

    SCREENSHOT

2. When the `Database Actions | Launchpad` tab opens, locate **Machine Learning** from the left nav menu within the **Development** section.

    SCREENSHOT

3. In the top right corner, ensure **Jupyter** is selected.

    SCREENSHOT

4. Install required, additional libraries for the workshop. Copy the code and press ▷ button. 

    ```
    <copy>
    ====================================!!!!!!!!===============================

    install langchain-oracledb sentence-transformers langchain-openai langchain tavily-python
    <copy>
    ```

## Task 4: Connect to the database and create VECTOR user

### Understanding the Dual-Connection Pattern

Because we run this workshop inside an **Oracle Machine Learning (OML) Notebook** on Autonomous Database, we can leverage an implicit connection to the database via `import oml` — no credentials or wallet needed. We use `oml.cursor()` for direct SQL operations throughout the workshop.

However, LangChain's `OracleVS` requires an **`oracledb.Connection`** object as its `client` parameter. Since `oml.cursor()` returns a `cx_Oracle` cursor (not an `oracledb` connection), we create a separate lightweight `oracledb` connection for LangChain.

> **Why two connections?** The OML connection is implicit and powers `oml.cursor()`, `oml.push()`, `oml.sync()`, etc. The `oracledb` connection is only needed to satisfy LangChain's type requirement. Both connect to the same database schema.

1. Copy the following into the first paragraph field and click the ▷ to run the code.

    ```python
    <copy>
    %python

    import oml
    import logging

    # OML notebooks are pre-connected — verify it
    print("OML connected:", oml.isconnected())

    # Use oml.cursor() for direct SQL
    cr = oml.cursor()
    cr.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
    banner = cr.fetchone()[0]
    print(f"\n{banner}")
    cr.close()
    </copy>
    ```

    SCREENSHOT

2. Now test the connection using the OracleDB driver for Python. Paste the following code and be sure to replace the `your_dsn` text with the value you copied in Task 2.

    ```python
    <copy>
    %python

    import oracledb

    # Store username, password, and DSN
    adb_user = "admin"
    adb_password = "WElcome123##"
    adb_dsn = "your_dsn"

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

    SCREENSHOT with full DSN

    SCREENSHOT of successful output

3. Create the VECTOR user.

    ```python
    <copy>
    %python

    def setup_oracle_adb(
        create_vector_user=True,
        vector_user="VECTOR",
        vector_password="MemoryContext_2026" 
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

    SCREENSHOT code output

You may now proceed to the next lab.

## Learn More



## Acknowledgements

- **Author** - Richmond Alake
- **Contributors** - Eli Schilling
- **Last Updated By/Date** - Published February, 2026