# Lab 6: Automated Tagging Enforcement

## Introduction

-- Implement automation with Events and Functions to stop / terminate resources that are not compliant with tagging policies



**Estimated Time:** TBD minutes

### Objectives

In this lab, you will:

- ...


### Prerequisites

This lab assumes you have:

- Completed the previous labs.
- ...

## Task 1: Create a scheduled Function to terminate resources

```python
## Script will terminate resources that are not tagged properly
## Change scope to compartment vs. tenancy for Sandbox instructions

import oci
import sys

# --- Configuration ---
# Replace with your tag namespace, key, and expected value (or check for key existence)
TAG_NAMESPACE = "YourTagNamespace" 
TAG_KEY = "ComplianceStatus"
COMPLIANT_VALUE = "Compliant" 
# Replace with your tenancy's root compartment OCID or a specific compartment OCID
TENANCY_OCID = "ocid1.tenancy.oc1..aaaaa..." 

# Initialize clients
try:
    config = oci.config.from_file()
    search_client = oci.resource_search.ResourceSearchClient(config)
    compute_client = oci.core.ComputeClient(config)
    # Use composite operations for waiting until termination is complete (optional)
    compute_composite_client = oci.core.ComputeClientCompositeOperations(compute_client)
except oci.exceptions.ConfigFileNotFound:
    print("OCI config file not found. Ensure ~/.oci/config is set up.")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing OCI clients: {e}")
    sys.exit(1)


def find_non_compliant_instances():
    """Finds all instances in the tenancy that do not have the specified compliant tag."""
    # RQS query to find all instances
    query = "query instance resources" 
    
    try:
        search_details = oci.resource_search.models.StructuredSearchDetails(query=query)
        # Search across all compartments in the tenancy
        resources = search_client.search_resources(search_details).data
        
        non_compliant_instances = []
        for resource in resources:
            is_compliant = False
            # Check for defined tags compliance
            defined_tags = resource.defined_tags.get(TAG_NAMESPACE, {})
            if defined_tags.get(TAG_KEY) == COMPLIANT_VALUE:
                is_compliant = True

            # If not compliant, add to the list
            if not is_compliant:
                non_compliant_instances.append(resource)
        
        return non_compliant_instances

    except oci.exceptions.ServiceError as e:
        print(f"Error during resource search: {e}")
        return []

def terminate_resource(instance_id):
    """Terminates a specific OCI compute instance."""
    print(f"Attempting to terminate instance OCID: {instance_id}")
    try:
        # Terminate and wait for state TERMINATED
        compute_composite_client.terminate_instance_and_wait_for_state(
            instance_id,
            wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED]
        )
        print(f"Successfully terminated instance: {instance_id}")
    except oci.exceptions.ServiceError as e:
        print(f"Failed to terminate instance {instance_id}: {e.message}")

if __name__ == "__main__":
    print(f"Scanning OCI tenancy for instances without compliant tag: {TAG_NAMESPACE}.{TAG_KEY}={COMPLIANT_VALUE}")
    untagged_resources = find_non_compliant_instances()
    
    if untagged_resources:
        print(f"Found {len(untagged_resources)} non-compliant instances.")
        for resource in untagged_resources:
            print(f"- Display Name: {resource.display_name}, OCID: {resource.identifier}")
            # Uncomment the following line to actually terminate the instances
            # terminate_resource(resource.identifier) 
        print("\nTermination calls made (if uncommented).")
    else:
        print("No non-compliant instances found.")
```

## Task 2: Create a custom function with Cloud Events

Using the code above, create another function for object storage buckets.
Adjust the code accordingly
Trigger the function using Cloud Events any time a new  bucket is created (or something like that) so it checks tags

You may now proceed to the next lab.

## Learn More


- [OCI CLI bulk-edit reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/iam/tag/bulk-edit.html)
- [Invoking Functions automatically with Cloud Events](https://blogs.oracle.com/developers/oracle-functions-invoking-functions-automatically-with-cloud-events)

## Acknowledgements

- **Author** - 
- **Contributors** - Daniel Hart, Deion Locklear, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2026