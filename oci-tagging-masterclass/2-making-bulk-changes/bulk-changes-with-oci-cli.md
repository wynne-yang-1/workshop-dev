# Lab 2: Making Bulk Changes to Tagged Resources

## Introduction

--Quick intro to OCI CLI (previewed last lab)
--What / Why bulk editing tags on resources
--References - to be removed before publishing:
    https://medium.com/@ralflange/tagging-resources-in-oracle-oci-3ded10c1e28f
    https://github.com/hoehenunterschied/OCI-Utilities/tree/main
    https://oracledbasjourney.wordpress.com/2023/05/10/update-multiple-created-tags/
    https://jasonlesterdba.wordpress.com/2025/03/18/individual-tag-updates-in-bulk/

In this lab you will provision a set of OCI resources (Compute instance, two Block Volumes, and an Object Storage bucket) and then use the OCI CLI to apply and modify defined tags on those resources in bulk. You will create one block volume attached to the compute instance and one unattached, plus an object storage bucket. After the resources are created, you will use the CLI to add defined tags and then alter them together.

**Estimated Time:** 20 minutes

### Objectives

In this lab, you will:

- Create resources
    - Compute Instance
    - 2 Block Volumes
    - Object Storage Bucket
- Use CLI to add / alter tags on the resources

### Prerequisites

This lab assumes you have:

- Completed the previous labs.
- ...

## Task 1: Create a Compute Instance

Use the OCI CLI to launch a compute instance. You must specify the compartment, subnet, image, and shape.

```bash
oci compute instance launch \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --display-name LabCompute1 \
  --availability-domain "yourAvailabilityDomain" \
  --subnet-id ocid1.subnet.oc1..yourSubnetOCID \
  --image-id ocid1.image.oc1..yourImageOCID \
  --shape VM.Standard.E2.1.Micro \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
  --wait-for-state RUNNING
```

Record the instance OCID from the command output for later tasks.

---

## Task 2: Create Two Block Volumes

Create two block volumes using the OCI CLI. One will be attached to the instance later.

```bash
oci bv volume create \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --availability-domain "yourAvailabilityDomain" \
  --size-in-gbs 50 \
  --display-name LabVolume1

oci bv volume create \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --availability-domain "yourAvailabilityDomain" \
  --size-in-gbs 50 \
  --display-name LabVolume2
```

Note the OCIDs for both volumes in the output.

---

## Task 3: Attach One Block Volume to the Instance

Attach the first block volume to your compute instance.

```bash
oci compute volume-attachment attach \
  --instance-id ocid1.instance.oc1..yourInstanceOCID \
  --volume-id ocid1.volume.oc1..yourVolume1OCID \
  --type paravirtualized
```

Ensure the volume attaches successfully before proceeding.

---

## Task 4: Create an Object Storage Bucket

Create an object storage bucket using the OCI CLI.

```bash
oci os bucket create \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --name lab-tagging-bucket
```

Record the bucket name and created bucket OCID if needed for future reference.

---

## Task 5: Prepare for Bulk Tagging

Create a `resources.json` file with all resource OCIDs and types:

```json
{
  "resources": [
    {
      "resourceId": "ocid1.instance.oc1..yourInstanceOCID",
      "resourceType": "Instance"
    },
    {
      "resourceId": "ocid1.volume.oc1..yourVolume1OCID",
      "resourceType": "BlockVolume"
    },
    {
      "resourceId": "ocid1.volume.oc1..yourVolume2OCID",
      "resourceType": "BlockVolume"
    },
    {
      "resourceId": "ocid1.bucket.oc1..yourBucketOCID",
      "resourceType": "ObjectStorageBucket"
    }
  ]
}
```

---

## Task 6: Apply Initial Defined Tags

Create `bulk-edit-add.json` to add defined tags:

```json
[
  {
    "definedTags": {
      "TagLabNS": {
        "Environment": "Dev",
        "Team": "CloudWorkshop"
      }
    },
    "operationType": "ADD_OR_SET"
  }
]
```

Run the bulk edit command:

```bash
oci iam tag bulk-edit \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --resources file://resources.json \
  --bulk-edit-operations file://bulk-edit-add.json \
  --wait-for-completion
```

---

## Task 7: Modify Tags in Bulk

Create `bulk-edit-update.json` to alter tag values:

```json
[
  {
    "definedTags": {
      "TagLabNS": {
        "Environment": "Test",
        "Team": "Platform"
      }
    },
    "operationType": "ADD_OR_SET"
  }
]
```

Run the bulk edit command again:

```bash
oci iam tag bulk-edit \
  --compartment-id ocid1.compartment.oc1..yourCompartmentOCID \
  --resources file://resources.json \
  --bulk-edit-operations file://bulk-edit-update.json \
  --wait-for-completion
```

---

## Task 8: Verify Tag Changes

Check the defined tags on each resource with CLI commands such as:

```bash
oci compute instance get --instance-id ocid1.instance.oc1..yourInstanceOCID --query "data.defined-tags"
oci bv volume get --volume-id ocid1.volume.oc1..yourVolume1OCID --query "data.defined-tags"
oci bv volume get --volume-id ocid1.volume.oc1..yourVolume2OCID --query "data.defined-tags"
oci os bucket get --namespace YourNamespace --name lab-tagging-bucket --query "data.defined-tags"
```

Confirm that all resources show the updated defined tag values.

---

## Learn More

- [Bulk Editing tags on resoruces using the OCI CLI](https://www.ateam-oracle.com/bulk-editing-tags-on-resources-using-the-oci-cli)
- [OCI CLI bulk-edit reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/iam/tag/bulk-edit.html)


## Acknowledgements

- **Author** - Daniel Hart
- **Contributors** - Deion Locklear, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2026
