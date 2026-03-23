# Lab 3: Import and Configure the OIC Weather API

## Introduction

In this lab, you will import a pre-built integration into Oracle Integration Cloud that exposes a weather reporting API. This integration calls the OpenWeather API to return weather data (temperature, description, coordinates) for a city you specify.

Rather than building the integration from scratch (which takes approximately 45 minutes), you will import a pre-built integration archive (IAR) file and configure it with your own OpenWeather API key. This approach saves time while still giving you hands-on experience with OIC projects, connections, and the integration activation workflow.

If you'd like to understand how this integration was built step-by-step, refer to the Oracle documentation: [Build Your Second Integration From Scratch](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/build-your-second-integration-scratch.html).

**Estimated Time:** 15 minutes

### Objectives

In this lab you will:

1. Download the pre-built Weather By City integration archive (IAR file)
2. Import the integration into an OIC project
3. Configure the OpenWeather API invoke connection with your API key
4. Activate and test the integration
5. Capture the OIC API endpoint URL for use in subsequent labs

### Prerequisites

This lab assumes you have:

* Completed the previous labs
* An active OIC instance (Generation 3 recommended)
* A free API key from [OpenWeather](https://home.openweathermap.org/)

## Task 1: Download the Pre-Built Integration

Download the pre-built Weather By City integration archive from the workshop resource bundle.

1. Locate the `WEATHER_BY_CITY_01.00.0000.iar` file in the workshop resource bundle provided by your instructor.
2. Save the file to a convenient location on your local machine.

<!-- AUTHOR NOTE:
     To create this IAR file, build the Weather By City integration per the Oracle
     tutorial linked above. Then export it from OIC:
     Project > Integrations > Actions menu (⋯) > Export.
     The IAR file will download to your local machine. Include this file in the
     workshop resource bundle distributed to attendees.
-->

> **What's inside the IAR file?** The integration archive contains the full integration definition, including the REST Adapter trigger connection (configured with OAuth 2.0 security), two invoke connections to the OpenWeather Geocoding and Weather APIs, all data mappings, and the business identifier configuration. Connections are included but require endpoint-specific credentials to be configured after import.

## Task 2: Create a Project and Import the Integration

1. Log in to your Oracle Integration Cloud instance.
2. In the navigation pane, click **Projects**.
3. Click **Add** and select **Create** to create a new project.
4. In the **Name** field, enter `Weather Workshop`.
5. Leave all remaining fields as they are, then click **Create**.
6. In the project's **Integrations** section, click **Add** and select **Import**.
7. Browse to and select the `WEATHER_BY_CITY_01.00.0000.iar` file you downloaded in Task 1.
8. Click **Import**.

    The Weather By City integration will appear in your project with a status of **Configured** (not yet active).

> **Note:** After importing, you must configure the connection endpoints before the integration can be activated. The connections are imported with the integration but require your specific credentials.

## Task 3: Configure the OpenWeather API Connection

The imported integration includes two connections: a **Rest_Trigger** (inbound) and a **Weather** invoke connection (outbound to OpenWeather). The trigger connection is pre-configured with OAuth 2.0 security and requires no changes. You need to configure the invoke connection with your API key.

1. In your project, navigate to the **Connections** section.
2. Click on the **Weather** connection (the invoke connection).
3. Verify or update the following fields:

    | Field | Value |
    |-------|-------|
    | **Connection Type** | REST API Base URL |
    | **Connection URL** | `https://api.openweathermap.org/` |
    | **Security Policy** | API Key Based Authentication |
    | **API Key** | *Paste your OpenWeather API key* |

4. Expand **Optional Security** and set the **API Key Usage** field:

    - For temperature in Fahrenheit: `?appid=${api-key}&units=imperial`
    - For temperature in Celsius: `?appid=${api-key}&units=metric`

5. Ensure **Access Type** is set to **Public Gateway**.
6. Click **Test** to validate the connection.

    You will see a success message noting that the API key itself is not validated as part of this test — this is expected behavior. The key is validated when the integration runs.

7. Click **Save**, then click **Back** to return to the project.

## Task 4: Activate and Test the Integration

1. In the **Integrations** section, locate the **Weather By City** integration.
2. Click the **Actions** menu (⋯) and select **Activate**.
3. Keep the tracing level set to **Production** and click **Activate**.
4. Click **Refresh** periodically and wait for the status to change to **Active**.
5. Click the **Actions** menu (⋯) and select **Run**.
6. On the **Configure and Run** page, enter a city name (e.g., `Seattle`) in the URI parameters section.
7. Click **Run**.
8. Review the **Activity Stream** panel — all milestones should be green, indicating a successful run.
9. Review the **Response** section at the bottom of the page. You should see a JSON response similar to:

    ```json
    {
      "city": "Seattle",
      "longitude": -122.3321,
      "latitude": 47.6062,
      "country": "US",
      "description": "overcast clouds",
      "temp": 52.3
    }
    ```

## Task 5: Capture the OIC API Endpoint URL

1. On the Configure and Run page, note the **GET URL** at the top. It will look something like:

    ```
    https://your-oic-instance.integration.oraclecloud.com/ic/api/integration/v2/flows/rest/WEATHER_BY_CITY/1.0/weather?city=Seattle
    ```

2. Save the following two values — you will need them in Lab 4:

    - **OIC hostname:** `your-oic-instance.integration.oraclecloud.com`
    - **Integration path:** `/ic/api/integration/v2/flows/rest/WEATHER_BY_CITY/1.0/weather`

## Lab 3 Recap

In this lab you brought your OIC backend to life:

* Created a new **OIC project** (`Weather Workshop`) and imported the pre-built Weather By City integration from an IAR file.
* Configured the **OpenWeather invoke connection** with your personal API key.
* **Activated** the integration and ran a successful end-to-end test, confirming that OIC calls the OpenWeather Geocoding API for coordinates, then the Weather API for current conditions, and returns a consolidated response.
* Captured your **OIC hostname** and **integration path**, which you will use to configure Traefik Hub routing in the next lab.

You may now proceed to the next lab.

## Learn More

* [Build Your Second Integration From Scratch (Oracle Docs)](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/build-your-second-integration-scratch.html)
* [Import and Export Integrations (Oracle Docs)](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/import-and-export-integrations.html)
* [About Projects in Oracle Integration](https://docs.oracle.com/en/cloud/paas/application-integration/integrations-user/integration-projects.html)

## Acknowledgements

* **Author(s)** - Eli Schilling & Vijaya Vishwanath
* **Contributors** - Carlos Villanua
* **Last Updated By/Date** - Published March 2026
