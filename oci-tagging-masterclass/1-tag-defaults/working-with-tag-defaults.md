# Lab 1: Working with Tag Defaults

## Introduction

--Overview of Tag defaults, where/how used, benefits, etc

**Estimated Time:** TBD minutes

### Objectives

In this lab, you will:

- Create a tag namespace
- Create tag key definition (static value & list of values)
- Review OCI Tag Namespace templates
- Assign Tag Defaults to compartment
- Validate enforcement by attempting to create Object Storage Bucket


### Prerequisites

This lab assumes you have:

- Completed the previous labs.
- ...

## Task 1: Sign into console and create tag namespace

## Task 3: Review OCI Tag Namespace Templates

    ```bash
    # List available tag namespace templates provided by Oracle

    oci iam standard-tag-namespace-template list-standard-tag-namespaces --all -c <paste compartment OCID here>
    ```

    ```bash
    # Get the details of a chosen tag namespace template
    # This example uses *Oracle-Standard* - feel free to choose a different option
    # or run the command multiple times to review different templates.

    oci iama standard-tag-namespace-template get-standrad-tag-template -c <paste compartment OCID here> --standard-tag-namespace-name Oracle-Standard
    ```

You may now proceed to the next lab.

## Learn More

- [Managing tag defaults](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/managingtagdefaults.htm)
- [Using tag variables](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/usingtagvariables.htm)
- [Assemble effective tag set with CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/iam/tag-default/assemble-effective-tag-set.html)
- [Working with OCI Tag Defaults in Terraform](https://medium.com/oracledevs/working-with-oci-tag-defaults-in-terraform-d07608564eaf)


## Acknowledgements

- **Author** - 
- **Contributors** - Daniel Hart, Deion Locklear, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2026