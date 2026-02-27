# Lab 3a (Tech): Working with Cost Management and Tags

## Introduction

In this lab, we are going to explain how to use cost-tracking tags, create a budget and budget alert rule, build and export a cost analysis report, and explain what FOCUS cost reports cover. 

**Estimated Time:** TBD minutes

### Objectives

In this lab, you will:

- Create a budget
- Create a budget alert rule
- Create a cost analysis report
- Download a FOCUS Report

### Prerequisites

This lab assumes you have:
- completed the previous labs
- permissions to interact with tools through Identity and Access Management policies

## Task 1: Ensure you have created a cost-tracking tag
In this task, we are readdressing cost tracking tags. Please refer to the cost-tracking tag previously created in Lab 1. This cost-tracking tag is used for tracking resource costs that span multiple compartments or belong to different Cost Centers. Cost-tracking tags are also used for billing purposes. However, you can use *any defined tag* as a scope for your budgets, Cost Analysis, and Cost Reports. 


## Task 2: Budgets
In this task we are going to create a budget based on a cost tracking tag and create a budget alert rule for the budget.
1. Click the **Navigation Menu** on the upper left. Navigate to **Billing & Cost Management**, and select **Budgets**
2. Make sure you are in the correct region on the upper left.
3. Click Create Compartment.
4. Select Tags as the Budget Scope.
5. Select the Tag Namespace and Tag Key for the cost-tracking tag you created earlier. Select the value you would like to set for the budget scope.
6. Select Monthly for Schedule.
7. Enter $1 as the Budget Amount.
8. Select xxxx as the day of the month for recurring budget processing.
The budget will now evaluate consumption costs for resources under your cost-tracking tag every month on the xxth.
We will now create a Budget Alert Rule for this budget. You can also create Budget Alert Rules after you have created your budget.
9. Select Actual Spend for the Threshold Metric for the Budget Alert Rule.
10. Select Percentage of Budget as Threshold Type.
11. Input 1% as the threshold % amount.
12. Input email recipient for the budget alert.
13. Input email message:

      ```text
      <copy>
      Hello, you are receiving this message because your budget has been reached. 
      </copy>
      ```

> **Note:** Your budget alert notification may not be delivered right away. We have included an image of what a delivered budget rule notification looks like. 

Click [here] to download an image of a budget alert notification. 
You have now created your first budget and budget alert rule. 

You may now proceed to the next lab.


## Task 3: Cost Analysis & Reports
In this task, we are going to generate a cost analysis report using filters and dimensions and export the generated report. We are also going to view and download a FOCUS cost report. 

1. Click the **Navigation Menu** on the upper left. Navigate to **Billing & Cost Management**, and select **Cost Analysis**
2. Click Add Filter then click Tag. 
3. Input the Tag Namespace and Tag Key for the cost-tracking tag that you created earlier. 
4. Keep it as Match any value.
5. Click Select.
6. Click Grouping Dimensions then click Region.
7. Click Apply.
You should see the generated cost analysis based on your filter and grouping dimension selections.
8. Click on Bars to change the visualization to Lines. 
9. Click on Tab Actions to download your visualization to your local machine.
Next, we will download and view a FOCUS cost report.
10. Click the **Navigation Menu** on the upper left. Navigate to **Billing & Cost Management**, and select **Cost and Usage Reports**.
11. Navigate to **FOCUS Reports** and click the arrow to expand it.
> **Note:** FOCUS Reports are organized by year, month, day, and multiple time stamps during the day. 
12. Once you have decided on a FOCUS cost report to download, click on the 3 dots to the right side of the report. Click Download Report to download your FOCUS cost report to your local machine.
13. Open the FOCUS cost report file you just downloaded. 

The FOCUS report contains data on resource usage and consumption costs in your tenancy. This data is stored in OCI Object Storage and can easily be used to build visual dashboards in Oracle native services such as Oracle Analytics Cloud. You can also import FOCUS cost reports to third party tools to digest and analyze data contents.

> **Note:** Your tenancy may not have generated any FOCUS cost reports yet. We have included a FOCUS cost report file for you to view. Click [here] to download a FOCUS cost report csv file. The FOCUS cost report has many columns but here are some important ones to note: UsageQuantity, Tags, PricingUnit, ListUnitPrice, BilledCost.

You have now generated your first cost analysis report and downloaded a FOCUS cost report. 

Congratulations! You may move on to the next part of the lab. 

## Learn More

- [Using Cost Tracking Tags](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/usingcosttrackingtags.htm)
- [Quickly and easily apply budgets to manage OCI spending](https://www.ateam-oracle.com/apply-budgets-easily)
- [FOCUS Cost Reports Explained](https://blogs.oracle.com/cloud-infrastructure/announcing-focus-support-for-oci-cost-reports)
- [Creating a Budget](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/create-budget.htm)
- [How to use Cost Analysis](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/costanalysisoverview.htm)

## Acknowledgements

- **Author** - Wynne Yang
- **Contributors** - Daniel Hart, Deion Locklear, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2026