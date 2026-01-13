# Introduction to tagging

Tagging plays a crucial role in organizing and managing cloud resources. A tag is essentially a key value pair that can be added to cloud resources to enhance control. In Oracle Cloud Infrastructure (OCI), tagging is built into the Identity and Access Management (IAM) service, enabling users to systematically categorize and manage resources. The use of tagging further allows for activities such as cost tracking, resource discovery and management, filtering, and logical organization. 

## Key Features

- **Tag types:** OCI provides the ability to create both free-form tags and defined tags. A free-form tag includes just key and value and can be added to resources as necessary. Defined tags are created by the administrator, enabling a greater level of control and consistency. Defined tags include a tag namespace, a tag key, and a tag value. The tag value can be free-form or a pre-defined list of values.
- **Cost tracking tags:** Cost tracking is a feature of defined tags. You can enable up to 10 tag key definitions to use for cost-tracking purposes. When assigned to a resource, the cost-tracking tags will appear in billing and cost management.
- **Tag defaults:** Enables administrators to automatically apply tags to all resources in a compartment at the time of creation. This feature can be used to enforce tagging requirements throughout your OCI tenancy.
- **Tag variables:** A variable can be assigned to the value of a defined tag. When a resource is tagged, the variable will resolve to a text value. For example `${iam.principal.name}` will resolve to the name of the user that applied the tag to the resource.

When working with tags, there are a number of additional services that can be utilized to provide additional management and automation capabilities:

- **Budgets:** A cost-management feature that enables administrators to set spending limits, track costs, and generate automated alerts to help prevent overspending.
- **Cloud Events:** Enables administrators to create automation based on state chagnes of resources within the tenancy. 
- **Functions:** A serverless, event-driven platform that can be used to automate simple tasks. Functions can be scheduled or triggered by the Events service. These light-weight, serverless programs can be used to maintain or destroy resources based on tags.

## About this Workshop

This workshop will provide a framework for understanding the array of capabilities enabled through the implemention of a comprehensive tagging strategy. It will explore a variety of use cases that can enable organizations to:
- improve visibility of resources
- reduce administrative overhead of managing large pools of resources
- simplify cost management activities
- control / mitigate overspending
- provide additional flexibility in managaing access controls

**Estimated Workshop Time:** 2 hours 15 minutes

## Objectives

In this workshop, you will learn how to:

- Create free form and defined tags.
- Designate defined tags as cost tracking tags.
- Define tag defaults in a compartment.
- Utilize the OCI command line interface (CLI) to perform bulk changes to resources based on tags.
- Implement cost management features using tags.
- Leverage tags to define access control policies within IAM.
- Provision serverless functions to update / manage tags on a scheduled basis.
- Provision serverless functions to automatically stop / terminate resources based on tags.


## Learn More

- [Overview of tagging](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm)
- [Tagging best practices](https://www.ateam-oracle.com/oracle-cloud-infrastructure-tagging-best-practices-enable-mandatory-tagging-for-compartments)
- [OCI Command Line Interface](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm)
- [OCI Budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm)
- [OCI Events](https://docs.oracle.com/en-us/iaas/Content/Events/Concepts/eventsoverview.htm)
- [OCI Funtions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)

## Acknowledgements

- **Author** - Eli Schilling
- **Contributors** - 
