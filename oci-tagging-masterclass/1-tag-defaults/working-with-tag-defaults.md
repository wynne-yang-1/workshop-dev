# Lab 1: Working with Tag Defaults

## Introduction

In this lab, you will create and manage Defined Tags and Tag Defaults in Oracle Cloud Infrastructure (OCI). Tag Defaults enable administrators to automatically apply required tags to resources created within a specific compartment. This ensures governance, standardization, and cost visibility across your environment.
You will create a tag namespace, define tag keys, assign tag defaults to a compartment, and validate enforcement by creating a resource.

**Estimated Time:** 20–25 minutes

### Objectives

In this lab, you will:

- Create a tag namespace
- Create tag key definitions (static and list-based values)
- Review OCI Tag Namespace templates
- Assign Tag Defaults to a compartment
- Validate enforcement by creating an Object Storage bucket

### Prerequisites

This lab assumes you have:

- Completed previous labs
- Administrative access to IAM and compartments
- OCI CLI installed and configured (optional for CLI steps)

## Task 1: Create a Tag Namespace

Tag namespaces logically group related tag keys. All defined tags must belong to a namespace.

### Console Steps

1. Open the OCI Console.

2. Navigate to **Identity & Security**.

3. Select **Tag Namespaces**.

4. Click **Create Tag Namespace**.

5. Enter:

   **Name**:

    ```text
    <copy>
    'LLTagNamespace'
    </copy>
    ```

    **Description**:

     ```text
    <copy>
    My Tag Namespace
    </copy>
    ```

6. Ensure "Retired" is unchecked.
7. Click **Create**.
[Insert Screenshot – Creating Tag Namespace]
Verify the namespace appears in the list.

### CLI Method

 ```text
    <copy>
oci iam tag-namespace create 
–compartment-id <tenancy_ocid> 
–name LiveLabTagNS 
–description “Namespace for LiveLab tagging exercises” 
–is-retired false
</copy>
```
Verify:
oci iam tag-namespace list –compartment-id <tenancy_ocid>

## Task 2: Create Tag Key Definitions

Now that you have created a tag namespace, you will create tag keys inside that namespace.

A tag namespace is like a folder.  
A tag key is the actual label that gets attached to resources.

In this task, you will create:

- A general tag key called **CostCenter**
- A restricted tag key called **Environment**


OCI supports different types of tag validation:
- **No validation (flexible)** — Users can enter any value.
- **List of values (restricted)** — Users must select from predefined values.
Using list-based validation helps standardize tagging across teams.

## Task 2A: Create the CostCenter Tag

This tag will represent which department or business unit owns a resource.

### Console Steps

1. Navigate to **Identity & Security → Tag Namespaces**.

2. Select the namespace you created earlier (`LivelabTagNS`).

3. Click **Create Tag**.

4. Enter the following:
   **Name:**
   ```text
   <copy>
    CostCenter
    </copy>
    ```
   **Description:**
   ```text
   <copy>
   Identifies the business cost center
   </copy>
   ```
5. Leave the Validator section as default (no restrictions).

6. Click **Create**.

[Insert Screenshot – Creating CostCenter Tag]

The CostCenter tag can accept any value when applied to a resource, such as:
- Finance
- IT
- Marketing
- 1001
This provides flexibility for business labeling.

### CLI Method (Optional)

```text
<copy>
oci iam tag create 
–tag-namespace-id <tag_namespace_ocid> 
–name CostCenter 
–description “Identifies the business cost center”
</copy>
```

## Task 2B: Create the Environment Tag

This tag will identify the lifecycle stage of a resource.
To keep tagging consistent, you will restrict values to a predefined list.

### Console Steps

1. Still inside the `LivelabTagNS` namespace, click **Create Tag**.
2. Enter:

**Name:** 
   ```text
   <copy>
   Environment
   </copy> 
   ```
**Description:**
   ```text
   <copy>
   Identifies the environment of the resource
   </copy>
   ```
3. Under **Validator**, select **List of values**.

4. Add the following values:
   - Dev
   - Test
   - Prod

5. Click **Create**.

[Insert Screenshot – Creating Environment Tag with List Values]

When users apply this tag to a resource, they can only select:
- Dev
- Test
- Prod

This ensures consistent tagging and supports future policy enforcement.

### CLI Method (Optional)

```text
<copy>
oci iam tag create 
–tag-namespace-id <tag_namespace_ocid> 
–name Environment 
–description “Identifies the environment of the resource” 
–validator ‘{
“validatorType”:“ENUM”,
“values”:[“Dev”,“Test”,“Prod”]
}’
</copy>
```
**Verify Your Work**

At the end of this task, confirm that:
- Both `CostCenter` and `Environment` appear under your namespace.
- The Environment tag shows a list validator.
- Neither tag is marked as retired.
[Insert Screenshot – Tag List Showing Both Keys]

Tag keys define the structure for how resources are labeled.
In a later task, you will use these tag keys to automatically apply tags using Tag Defaults.

## Task 3: Review Tag Namespace Templates
Before applying tags broadly, it is helpful to understand that OCI provides built-in tag namespace templates.
Templates are pre-designed tagging structures that follow common governance patterns. They can help organizations get started quickly without designing a tagging structure from scratch.
In this task, you will explore available templates so you can see how OCI recommends structuring tags.

### Console Steps

1. Navigate to **Identity & Security → Tag Namespaces**.
2. At the top of the page, select **Templates**.
3. Review the available templates.
4. Click into one of the templates to see the tag keys it includes.
[Insert Screenshot – Viewing Tag Templates]

### CLI Method (Optional)
OCI CLI does not provide a direct “templates” browsing command like the Console UI.  
Instead, you can list the tag namespaces that currently exist in your tenancy. Some of these may have been created from templates.
1. List tag namespaces in the tenancy:
oci iam tag-namespace list –compartment-id <tenancy_ocid>
2. If you want to inspect a specific namespace in more detail, you can list the tags inside it:
oci iam tag list –tag-namespace-id <tag_namespace_ocid>
This CLI step is informational. Templates are primarily a Console-guided feature.

## Task 4: Assign Tag Defaults to a Compartment
Now that you have created tag keys, you will configure a Tag Default.
A Tag Default automatically applies a defined tag to all new resources created inside a specific compartment. This helps ensure consistent tagging without requiring users to manually tag every resource.

`What Is a Tag Default?`

**Without a Tag Default:**

Users must manually apply tags.
Tags might be forgotten or inconsistent.

**With a Tag Default:**

The tag is automatically added when a resource is created.
Governance becomes easier and more reliable.

### Console Steps
1. Navigate to **Governance & Administration → Tag Defaults**.
2. Click **Assign Tag Default**.
3. Select the compartment where you want the tag applied automatically.
4. Choose:
   - Tag Namespace: `LivelabTagNS`
   - Tag Key: `Environment`
   - Default Value: `Prod`
5. Click **Assign**.
[Insert Screenshot – Assigning Tag Default]
After assignment, confirm the Tag Default appears in the list for that compartment.

### CLI Method (Optional)
To create a tag default, you need the OCID of the tag key definition (Tag Definition OCID).
1. Get your Object Storage namespace (you will use this later as well):
```text
<copy>
oci os ns get
</copy>
```
2. List namespaces to find your namespace OCID:
```text
<copy>
oci iam tag-namespace list –compartment-id <tenancy_ocid>
</copy>
```
3. List tags under your namespace to find the tag definition OCID for `Environment`:
```text
<copy>
oci iam tag list –tag-namespace-id <tag_namespace_ocid>
</copy>
```
4. Create the tag default in the target compartment (example assigns `Prod`):

```text
<copy>
oci iam tag-default create 
–compartment-id <target_compartment_ocid> 
–tag-definition-id <environment_tag_definition_ocid> 
–value Prod
</copy>
```
5. Verify the tag default:
```text
<copy>
oci iam tag-default list –compartment-id <target_compartment_ocid>
</copy>
```
## Task 5: Validate Tag Default Enforcement
Now you will confirm that your Tag Default is working as expected.
You will create a new bucket in the compartment where you assigned the tag default, and then verify that the defined tag was applied automatically.

### Console Steps

1. Navigate to **Object Storage → Buckets**.
2. Click **Create Bucket**.
3. Select the same compartment where you applied the Tag Default.
4. Enter a bucket name (for example: `tag-test-bucket`).
5. Expand the **Defined Tags** section before creating the bucket.
[Insert Screenshot – Bucket Create Page Showing Defined Tags]
You should see the `Environment` tag pre-populated with the value `Prod`.
6. Click **Create**.
7. Open the bucket after it is created.
8. Scroll to the **Defined Tags** section and confirm the tag is present.
[Insert Screenshot – Bucket Details Showing Applied Tag]

### CLI Method (Optional)
1. Get your Object Storage namespace (if you did not already):
oci os ns get
2. Create a bucket in the compartment where the Tag Default is assigned:
oci os bucket create 
–compartment-id <target_compartment_ocid> 
–name tag-test-bucket-cli 
–namespace-name <object_storage_namespace>
3. Verify the bucket details and confirm the defined tag appears:
oci os bucket get 
–bucket-name tag-test-bucket-cli 
–namespace-name <object_storage_namespace>
In the output, look for the `defined-tags` section and confirm it includes something similar to:
- Namespace: `LivelabTagNS`
- Key: `Environment`
- Value: `Prod`

### Check Your Work
You should now have:
- A tag default assigned to your compartment
- A newly created bucket that automatically received the defined tag
- Confirmation in either the Console or CLI that tagging occurred automatically

## Summary
In this lab, you:
- Created a tag namespace
- Created static and list-based tag keys
- Reviewed tag templates
- Applied tag defaults to a compartment
- Validated automatic tag enforcement

Tag defaults improve governance, consistency, and cost management across OCI environments.

## Learn More

- [Managing tag defaults](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/managingtagdefaults.htm)
- [Using tag variables](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/usingtagvariables.htm)
- [Assemble effective tag set with CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/iam/tag-default/assemble-effective-tag-set.html)
- [Working with OCI Tag Defaults in Terraform](https://medium.com/oracledevs/working-with-oci-tag-defaults-in-terraform-d07608564eaf)


## Acknowledgements

- **Author** - Deion Locklear
- **Contributors** - Daniel Hart, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2026