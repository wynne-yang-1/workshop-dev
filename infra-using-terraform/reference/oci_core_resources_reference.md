# OCI Terraform Provider — CORE Resources: Attribute Reference

> **Purpose:** Workshop quick-reference for all major resources in the **Core** service of the Oracle Cloud Infrastructure (OCI) Terraform provider. Each resource lists its configurable attributes, whether the attribute is required or optional, and whether it can be updated in-place. Attributes **not** marked as updatable will force the resource to be **destroyed and recreated** when changed.
>
> **Source:** [Oracle Cloud Infrastructure Terraform Provider Documentation](https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/)

---

## oci_core_vcn

Creates a Virtual Cloud Network (VCN).

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `cidr_block` | Optional (deprecated — use `cidr_blocks`) | No |
| `cidr_blocks` | Optional | Yes |
| `byoipv6cidr_details` | Optional | No |
| `byoipv6cidr_details.byoipv6range_id` | Required (within block) | No |
| `byoipv6cidr_details.ipv6cidr_block` | Required (within block) | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `dns_label` | Optional | No |
| `freeform_tags` | Optional | Yes |
| `ipv6private_cidr_blocks` | Optional | No |
| `is_ipv6enabled` | Optional | No |
| `is_oracle_gua_allocation_enabled` | Optional | No |
| `security_attributes` | Optional | Yes |

---

## oci_core_subnet

Creates a subnet in a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | No |
| `vcn_id` | Required | No |
| `availability_domain` | Optional | No |
| `cidr_block` | Optional | No |
| `defined_tags` | Optional | Yes |
| `dhcp_options_id` | Optional | Yes |
| `display_name` | Optional | Yes |
| `dns_label` | Optional | No |
| `freeform_tags` | Optional | Yes |
| `ipv4cidr_blocks` | Optional | No |
| `ipv6cidr_block` | Optional | Yes |
| `ipv6cidr_blocks` | Optional | Yes |
| `prohibit_internet_ingress` | Optional | No |
| `prohibit_public_ip_on_vnic` | Optional | No |
| `route_table_id` | Optional | Yes |
| `security_list_ids` | Optional | Yes |

---

## oci_core_instance

Creates a compute instance.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `availability_domain` | Required | No |
| `compartment_id` | Required | Yes |
| `shape` | Required | Yes |
| `agent_config` | Optional | Yes |
| `agent_config.are_all_plugins_disabled` | Optional | Yes |
| `agent_config.is_management_disabled` | Optional | Yes |
| `agent_config.is_monitoring_disabled` | Optional | Yes |
| `agent_config.plugins_config` | Optional | Yes |
| `availability_config` | Optional | Yes |
| `availability_config.is_live_migration_preferred` | Optional | Yes |
| `availability_config.recovery_action` | Optional | Yes |
| `capacity_reservation_id` | Optional | Yes |
| `cluster_placement_group_id` | Optional | No |
| `compute_cluster_id` | Optional | No |
| `compute_host_group_id` | Optional | No |
| `create_vnic_details` | Optional | Yes |
| `create_vnic_details.assign_ipv6ip` | Optional | No |
| `create_vnic_details.assign_private_dns_record` | Optional | No |
| `create_vnic_details.assign_public_ip` | Optional | Yes |
| `create_vnic_details.defined_tags` | Optional | Yes |
| `create_vnic_details.display_name` | Optional | Yes |
| `create_vnic_details.freeform_tags` | Optional | Yes |
| `create_vnic_details.hostname_label` | Optional | Yes |
| `create_vnic_details.nsg_ids` | Optional | Yes |
| `create_vnic_details.private_ip` | Optional | No |
| `create_vnic_details.skip_source_dest_check` | Optional | Yes |
| `create_vnic_details.subnet_cidr` | Optional | No |
| `create_vnic_details.subnet_id` | Optional | No |
| `create_vnic_details.vlan_id` | Optional | No |
| `dedicated_vm_host_id` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `extended_metadata` | Optional | Yes |
| `fault_domain` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `hostname_label` | Optional | No |
| `image` | Optional (deprecated) | No |
| `instance_configuration_id` | Optional | No |
| `instance_options` | Optional | Yes |
| `instance_options.are_legacy_imds_endpoints_disabled` | Optional | Yes |
| `ipxe_script` | Optional | No |
| `is_ai_enterprise_enabled` | Optional | Yes |
| `is_pv_encryption_in_transit_enabled` | Optional | No |
| `launch_options` | Optional | Yes (partial) |
| `launch_options.boot_volume_type` | Optional | Yes |
| `launch_options.firmware` | Optional | No |
| `launch_options.is_consistent_volume_naming_enabled` | Optional | No |
| `launch_options.is_pv_encryption_in_transit_enabled` | Optional | Yes |
| `launch_options.network_type` | Optional | Yes |
| `launch_options.remote_data_volume_type` | Optional | No |
| `launch_volume_attachments` | Optional | No |
| `licensing_configs` | Optional | Yes |
| `licensing_configs.type` | Required (within block) | Yes |
| `licensing_configs.license_type` | Optional | Yes |
| `metadata` | Optional | Yes |
| `placement_constraint_details` | Optional | No |
| `platform_config` | Optional | Yes (partial) |
| `platform_config.type` | Required (within block) | No |
| `platform_config.is_measured_boot_enabled` | Optional | No |
| `platform_config.is_memory_encryption_enabled` | Optional | No |
| `platform_config.is_secure_boot_enabled` | Optional | No |
| `preemptible_instance_config` | Optional | No |
| `security_attributes` | Optional | No |
| `shape_config` | Optional | Yes |
| `shape_config.baseline_ocpu_utilization` | Optional | Yes |
| `shape_config.memory_in_gbs` | Optional | Yes |
| `shape_config.nvmes` | Optional | Yes |
| `shape_config.ocpus` | Optional | Yes |
| `shape_config.vcpus` | Optional | Yes |
| `source_details` | Optional | Yes (partial) |
| `source_details.source_id` | Required (within block) | No |
| `source_details.source_type` | Required (within block) | No |
| `source_details.boot_volume_size_in_gbs` | Optional | No |
| `source_details.boot_volume_vpus_per_gb` | Optional | No |
| `source_details.kms_key_id` | Optional | No |
| `state` | Optional | Yes |
| `preserve_boot_volume` | Optional | N/A (destroy-time only) |
| `async` | Optional | N/A (behavior flag) |

---

## oci_core_volume

Creates a block volume.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `availability_domain` | Optional | No |
| `compartment_id` | Required | Yes |
| `autotune_policies` | Optional | Yes |
| `autotune_policies.autotune_type` | Required (within block) | Yes |
| `autotune_policies.max_vpus_per_gb` | Required (when PERFORMANCE_BASED) | Yes |
| `backup_policy_id` | Optional (deprecated) | No |
| `block_volume_replicas` | Optional | Yes |
| `cluster_placement_group_id` | Optional | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `is_auto_tune_enabled` | Optional | Yes |
| `kms_key_id` | Optional | Yes |
| `size_in_gbs` | Optional | Yes |
| `size_in_mbs` | Optional (deprecated) | No |
| `source_details` | Optional | No |
| `source_details.id` | Required (within block) | No |
| `source_details.type` | Required (within block) | No |
| `volume_backup_id` | Optional (deprecated) | No |
| `vpus_per_gb` | Optional | Yes |
| `xrc_kms_key_id` | Optional | No |

---

## oci_core_boot_volume

Creates a boot volume.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `source_details` | Required | No |
| `source_details.id` | Required (within block) | No |
| `source_details.type` | Required (within block) | No |
| `autotune_policies` | Optional | Yes |
| `autotune_policies.autotune_type` | Required (within block) | Yes |
| `autotune_policies.max_vpus_per_gb` | Required (when PERFORMANCE_BASED) | Yes |
| `availability_domain` | Optional | No |
| `backup_policy_id` | Optional | No |
| `boot_volume_replicas` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `is_auto_tune_enabled` | Optional | Yes |
| `kms_key_id` | Optional | Yes |
| `size_in_gbs` | Optional | Yes |
| `vpus_per_gb` | Optional | Yes |

---

## oci_core_volume_group

Creates a volume group.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `availability_domain` | Required | No |
| `compartment_id` | Required | Yes |
| `source_details` | Required | No |
| `source_details.type` | Required (within block) | No |
| `source_details.volume_ids` | Required (when type=volumeIds) | No |
| `source_details.volume_group_backup_id` | Required (when type=volumeGroupBackupId) | No |
| `source_details.volume_group_id` | Required (when type=volumeGroupId) | No |
| `backup_policy_id` | Optional (deprecated) | No |
| `cluster_placement_group_id` | Optional | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `volume_group_replicas` | Optional | Yes |
| `volume_ids` | Optional (update only) | Yes |
| `xrr_kms_key_id` | Optional | Yes |
| `xrc_kms_key_id` | Optional | No |

---

## oci_core_volume_backup_policy

Creates a user-defined volume backup policy.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `destination_region` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `schedules` | Optional | Yes |
| `schedules.backup_type` | Required (within block) | Yes |
| `schedules.period` | Required (within block) | Yes |
| `schedules.retention_seconds` | Required (within block) | Yes |
| `schedules.day_of_month` | Optional | Yes |
| `schedules.day_of_week` | Optional | Yes |
| `schedules.hour_of_day` | Optional | Yes |
| `schedules.month` | Optional | Yes |
| `schedules.offset_seconds` | Optional | Yes |
| `schedules.offset_type` | Optional | Yes |
| `schedules.time_zone` | Optional | Yes |

---

## oci_core_internet_gateway

Creates an internet gateway for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `enabled` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `route_table_id` | Optional | Yes |

---

## oci_core_nat_gateway

Creates a NAT gateway for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `block_traffic` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `public_ip_id` | Optional | No |
| `route_table_id` | Optional | Yes |

---

## oci_core_service_gateway

Creates a service gateway for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `services` | Required | Yes |
| `services.service_id` | Required (within block) | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `route_table_id` | Optional | Yes |

---

## oci_core_route_table

Creates a route table for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `route_rules` | Optional | Yes |
| `route_rules.network_entity_id` | Required (within block) | Yes |
| `route_rules.destination` | Optional | Yes |
| `route_rules.destination_type` | Optional | Yes |
| `route_rules.description` | Optional | Yes |

---

## oci_core_security_list

Creates a security list for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `egress_security_rules` | Optional | Yes |
| `egress_security_rules.destination` | Required (within block) | Yes |
| `egress_security_rules.protocol` | Required (within block) | Yes |
| `egress_security_rules.destination_type` | Optional | Yes |
| `egress_security_rules.stateless` | Optional | Yes |
| `egress_security_rules.icmp_options` | Optional | Yes |
| `egress_security_rules.tcp_options` | Optional | Yes |
| `egress_security_rules.udp_options` | Optional | Yes |
| `ingress_security_rules` | Optional | Yes |
| `ingress_security_rules.source` | Required (within block) | Yes |
| `ingress_security_rules.protocol` | Required (within block) | Yes |
| `ingress_security_rules.source_type` | Optional | Yes |
| `ingress_security_rules.stateless` | Optional | Yes |
| `ingress_security_rules.icmp_options` | Optional | Yes |
| `ingress_security_rules.tcp_options` | Optional | Yes |
| `ingress_security_rules.udp_options` | Optional | Yes |

---

## oci_core_network_security_group

Creates a network security group (NSG) for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_network_security_group_security_rule

Creates a security rule within an NSG.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `network_security_group_id` | Required | No |
| `direction` | Required | No |
| `protocol` | Required | No |
| `description` | Optional | No |
| `destination` | Optional (required if EGRESS) | No |
| `destination_type` | Optional | No |
| `source` | Optional (required if INGRESS) | No |
| `source_type` | Optional | No |
| `stateless` | Optional | No |
| `icmp_options` | Optional | No |
| `icmp_options.type` | Required (within block) | No |
| `icmp_options.code` | Optional | No |
| `tcp_options` | Optional | No |
| `udp_options` | Optional | No |

---

## oci_core_dhcp_options

Creates DHCP options for a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `options` | Required | Yes |
| `options.type` | Required (within block) | Yes |
| `options.server_type` | Optional | Yes |
| `options.custom_dns_servers` | Optional | Yes |
| `options.search_domain_names` | Optional | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_drg

Creates a Dynamic Routing Gateway (DRG).

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_drg_attachment

Creates a DRG attachment to a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `drg_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `drg_route_table_id` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `network_details` | Optional | Yes (partial) |
| `network_details.id` | Required (within block) | No |
| `network_details.type` | Required (within block) | No |
| `network_details.route_table_id` | Optional | Yes |
| `vcn_id` | Optional (deprecated) | No |

---

## oci_core_local_peering_gateway

Creates a local peering gateway (LPG) for VCN peering within a region.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `peer_id` | Optional | No |
| `route_table_id` | Optional | Yes |

---

## oci_core_remote_peering_connection

Creates a remote peering connection for cross-region VCN peering.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `drg_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `peer_id` | Optional | No |
| `peer_region_name` | Optional | No |

---

## oci_core_cpe

Creates a Customer-Premises Equipment (CPE) object for VPN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `ip_address` | Required | No |
| `cpe_device_shape_id` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `is_private` | Optional | No |

---

## oci_core_ipsec

Creates an IPSec VPN connection.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `cpe_id` | Required | No |
| `drg_id` | Required | No |
| `static_routes` | Required | No |
| `cpe_local_identifier` | Optional | Yes |
| `cpe_local_identifier_type` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_public_ip

Creates a reserved or ephemeral public IP.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `lifetime` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `private_ip_id` | Optional | Yes |
| `public_ip_pool_id` | Optional | No |

---

## oci_core_private_ip

Creates a secondary private IP on a VNIC.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `vnic_id` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `hostname_label` | Optional | Yes |
| `ip_address` | Optional | No |
| `vlan_id` | Optional | No |

---

## oci_core_vnic_attachment

Creates a secondary VNIC attachment on an instance.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `create_vnic_details` | Required | Yes (partial) |
| `create_vnic_details.assign_public_ip` | Optional | No |
| `create_vnic_details.defined_tags` | Optional | Yes |
| `create_vnic_details.display_name` | Optional | Yes |
| `create_vnic_details.freeform_tags` | Optional | Yes |
| `create_vnic_details.hostname_label` | Optional | Yes |
| `create_vnic_details.nsg_ids` | Optional | Yes |
| `create_vnic_details.private_ip` | Optional | No |
| `create_vnic_details.skip_source_dest_check` | Optional | Yes |
| `create_vnic_details.subnet_id` | Optional | No |
| `create_vnic_details.vlan_id` | Optional | No |
| `instance_id` | Required | No |
| `display_name` | Optional | No |
| `nic_index` | Optional | No |

---

## oci_core_volume_attachment

Attaches a block volume to an instance.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `attachment_type` | Required | No |
| `instance_id` | Required | No |
| `volume_id` | Required | No |
| `device` | Optional | No |
| `display_name` | Optional | No |
| `encryption_in_transit_type` | Optional | No |
| `is_agent_auto_iscsi_login_enabled` | Optional | No |
| `is_pv_encryption_in_transit_enabled` | Optional | No |
| `is_read_only` | Optional | No |
| `is_shareable` | Optional | No |
| `use_chap` | Optional | No |

---

## oci_core_boot_volume_attachment

Attaches a boot volume to an instance.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `boot_volume_id` | Required | No |
| `instance_id` | Required | No |
| `display_name` | Optional | No |
| `encryption_in_transit_type` | Optional | No |

---

## oci_core_image

Creates a custom image from an instance or imports an image.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `image_source_details` | Optional | No |
| `image_source_details.source_type` | Required (within block) | No |
| `instance_id` | Optional | No |
| `launch_mode` | Optional | No |

---

## oci_core_instance_configuration

Creates an instance configuration template.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `instance_details` | Optional | No |
| `instance_id` | Optional | No |
| `source` | Optional | No |

---

## oci_core_instance_pool

Creates an instance pool.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `instance_configuration_id` | Required | Yes |
| `placement_configurations` | Required | Yes |
| `size` | Required | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `state` | Optional | Yes |

---

## oci_core_cluster_network

Creates a cluster network.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `instance_pools` | Required | Yes (partial) |
| `instance_pools.instance_configuration_id` | Required | Yes |
| `instance_pools.size` | Required | Yes |
| `placement_configuration` | Required | No |
| `placement_configuration.availability_domain` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_dedicated_vm_host

Creates a dedicated VM host.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `availability_domain` | Required | No |
| `compartment_id` | Required | Yes |
| `dedicated_vm_host_shape` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `fault_domain` | Optional | No |
| `freeform_tags` | Optional | Yes |

---

## oci_core_vlan

Creates a VLAN in a VCN.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `cidr_block` | Required | Yes |
| `compartment_id` | Required | Yes |
| `vcn_id` | Required | No |
| `availability_domain` | Optional | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `nsg_ids` | Optional | Yes |
| `route_table_id` | Optional | Yes |
| `vlan_tag` | Optional | No |

---

## oci_core_capture_filter

Creates a capture filter for VTAPs.

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `filter_type` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `vtap_capture_filter_rules` | Optional | Yes |
| `flow_log_capture_filter_rules` | Optional | Yes |

---

## oci_core_cross_connect

Creates a cross-connect (FastConnect physical port).

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `cross_connect_group_id` | Required | No |
| `far_cross_connect_or_cross_connect_group_id` | Optional | No |
| `location_name` | Required | No |
| `near_cross_connect_or_cross_connect_group_id` | Optional | No |
| `port_speed_shape_name` | Required | No |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `is_active` | Optional | Yes |

---

## oci_core_cross_connect_group

Creates a cross-connect group (LAG for FastConnect).

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |

---

## oci_core_virtual_circuit

Creates a virtual circuit (FastConnect logical connection).

| Attribute | Required / Optional | Updatable |
|---|---|---|
| `compartment_id` | Required | Yes |
| `type` | Required | No |
| `bandwidth_shape_name` | Optional | Yes |
| `cross_connect_mappings` | Optional | Yes |
| `customer_bgp_asn` | Optional | Yes |
| `defined_tags` | Optional | Yes |
| `display_name` | Optional | Yes |
| `freeform_tags` | Optional | Yes |
| `gateway_id` | Optional | Yes |
| `provider_service_id` | Optional | No |
| `region` | Optional | No |
| `routing_policy` | Optional | Yes |

---

> **Important Reminder:** For any attribute in the tables above that is **not** marked as Updatable (i.e., "No"), changing its value in your Terraform configuration will result in the resource being **destroyed and recreated**. Always run `terraform plan` before `terraform apply` to verify whether a change will be in-place or destructive.
>
> For the full and most current documentation, refer to the [OCI Terraform Provider Reference](https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/).
