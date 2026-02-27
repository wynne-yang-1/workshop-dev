# Lab 4: Tag-Based Access Control

## Introduction
In this lab, you will use Defined Tags within IAM policies to control access to resources in Oracle Cloud Infrastructure (OCI).

Tag-based access control allows administrators to grant or restrict permissions based on tag values instead of only using compartments. This provides more flexible and scalable governance.

You will apply a defined tag to a resource, create a test group and user, create an IAM policy using a tag condition, and validate that access is restricted based on the tag value.

**Estimated Time:** 25–30 minutes

### Objectives
In this lab, you will:
- Apply a defined tag to a resource
- Create a test group and user
- Create a tag-based IAM policy
- Restrict deletion of a tagged resource
- Validate access control behavior

### Prerequisites
This lab assumes you have:
- Completed previous tagging labs
- A defined tag namespace and tag key already created
- Administrative access to IAM
- OCI CLI installed and configured (optional for CLI steps)

## Task 1: Create a Test Resource

Before applying tag-based access control, you need a resource to test against.
In this task, you will create an Object Storage bucket that will later be protected by a tag-based policy.

### Console Steps
1. Navigate to **Object Storage → Buckets**.
2. Click **Create Bucket**.
3. Select your lab compartment.
4. Enter **Bucket Name:**
   ```text
   <copy>
   prod-bucket
   </copy>
   ```
Click Create.
[Insert Screenshot – Creating Test Bucket]

### CLI Method (Optional)
```text
<copy>
oci os bucket create
–compartment-id <compartment_ocid>
–name prod-bucket-cli
–namespace-name <object_storage_namespace>
</copy>
```
## Task 2: Apply a Defined Tag to the Resource

Now you will apply a defined tag to the bucket.
This tag will later be used inside an IAM policy to control access.

### Console Steps

1. Open the **prod-bucket**.
2. Scroll to the Defined Tags section.
3. Click **Edit Tags**.
4. **Select:**
    Namespace: LivelabTagNS
    Key: Environment
    Value: Prod

5. Click **Save Changes**.
[Insert Screenshot – Applying Defined Tag to Bucket]

The bucket is now labeled as a Production resource.
### CLI Method (Optional)
```text
<copy>
oci os bucket update
–bucket-name prod-bucket-cli
–namespace-name <object_storage_namespace>
–defined-tags ‘{
“LivelabTagNS”:{
“Environment”:“Prod”
}
}’
</copy>
```
## Task 3: Create a Test Group and User
To validate tag-based access control, you will create a separate group and user.
This user will attempt to delete the tagged resource.
Console Steps

1. **Navigate to Identity & Security → Groups**.
2. Click **Create Group**.
3. Enter:
     **Name:**
    ```text
    <copy>
    TagTestUsers
    </copy>
    ```

4. Click **Create**.
5. Navigate to **Users**.
6. Click Create **User**.
7. Enter:
        **Name:**
    ```text
        <copy>
        tagtestuser
        </copy>
    ```


8. Click **Create**.
9. Add the user to the **TagTestUsers** group.
[Insert Screenshot – Creating Group and User]

### CLI Method (Optional)

```text
<copy>
oci iam group create
–name TagTestUsers
–description “Tag testing group”
</copy>
```
```text
<copy>
oci iam user create
–name tagtestuser
–description “Tag policy test user”
</copy>
```
```text
<copy>
oci iam group add-user
–group-id <group_ocid>
–user-id <user_ocid>
</copy>
```
## Task 4: Create a Tag-Based IAM Policy
Now you will create a policy that restricts deletion of resources tagged as Prod.
This policy allows management of Object Storage resources, except those tagged with Environment = Prod.

### Console Steps

1. Navigate to **Identity & Security → Policies**.
2. Click **Create Policy**.
3. Enter:
    
    **Name:**
        ```text
        <copy>
        TagDeleteRestrictionPolicy
        </copy>
        ```text

4. In the **policy statement field**, enter:

```text
<copy>
Allow group TagTestUsers to manage object-family in compartment <compartment_name> where target.resource.tag.LivelabTagNS.Environment != ‘Prod’
</copy>
```
5. Click **Create**.
[Insert Screenshot – Creating Tag-Based Policy]

This policy means:

The group can manage object storage resources, **except** those tagged as Production

### CLI Method (Optional)

```text
<copy>
oci iam policy create
–compartment-id <tenancy_ocid>
–name TagDeleteRestrictionPolicy
–description “Restrict delete if tagged Prod”
–statements ‘[
“Allow group TagTestUsers to manage object-family in compartment <compartment_name> where target.resource.tag.LivelabTagNS.Environment != ‘Prod’”
]’
</copy>
```

## Task 5: Validate Tag-Based Access Control
Now you will confirm that the policy is working.

### Console Validation

1. Sign out of the administrator account.
2. Sign in as **tagtestuser**.
3. Navigate to **Object Storage → Buckets**.
4. Attempt to **delete prod-bucket**.
5. You should receive a permissions error.
[Insert Screenshot – Access Denied Error]

This happens because the bucket is tagged as Prod, and the policy blocks deletion of Production resources.

### CLI Validation (Optional)

Using a configured CLI profile for tagtestuser:

```text
<copy>
oci os bucket delete
–bucket-name prod-bucket-cli
–namespace-name <object_storage_namespace>
</copy>
```
You should receive a “Not authorized” error.

## (Optional Test)

1. Log back in as **Administrator**.
2. Change the bucket tag value from **Prod to Dev**.
3. Log back in as **tagtestuser**.
4. Attempt deletion again. This time, deletion should succeed. This demonstrates how tag values directly influence access control.

**Check Your Work**


You should now have:

- A bucket tagged as Production
- A test group and user
- A tag-based IAM policy created
- Verified that deletion is blocked for Production-tagged resources
- Observed how changing the tag changes access behavior

## Summary
In this lab, you:

- Applied a defined tag to a resource
- Created a test group and user
- Created a tag-based IAM policy
- Restricted deletion based on tag value
- Validated dynamic access control behavior
- Tag-based access control allows you to move beyond compartment-only permissions and implement flexible, metadata-driven security in OCI.

## Learn More

- [Using tags to manage access](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/managingaccesswithtags.htm)
- [Concepts guide: Tag-based access control](https://docs.oracle.com/en/engineered-systems/private-cloud-appliance/3.0-latest/concept/concept-tag-access.html#tag-access-example-taggedtargetcompt)
- [Improving the Aministrative ... Experience ...](https://blogs.oracle.com/cloud-infrastructure/improving-console-experience-with-tbac-in-oci)

## Acknowledgements

- **Author** - Deion Locklear
- **Contributors** - Daniel Hart, Eli Schilling, Wynne Yang
- **Last Updated By/Date** - Published February, 2025