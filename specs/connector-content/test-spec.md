# CONN-EGERIA-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |

## Rows awaiting bound tests

- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R002`: planned proof `tests/test_access_contracts.py::test_catalog_contracts_certified`. Expected: Rollup closes when `.1` to `.4` are verified. Root test: `tests/test_access_contracts.py::test_catalog_contracts_certified`.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R002.1`: planned proof `tests/test_instance_header.py::test_records_keep_guid_type_and_version`. Expected: Each mapped record holds the four header fields.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R002.2`: planned proof `tests/test_access_contracts.py::test_catalog_contracts_certified`. Expected: Each contract names an existing tool.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R002.3`: planned proof `tests/test_access_contracts.py::test_catalog_recordings_validate`. Expected: A recording without `version` fails certification.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R002.4`: planned proof `tests/test_ontology_rollup.py::test_catalog_classes_roll_up_to_engine_terms`. Expected: Every catalog class has one engine ancestor.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R003`: planned proof `tests/test_catalog_write_sink.py::test_released_changes_apply_with_version_check`. Expected: Rollup closes when `.1` to `.3` are verified. Root test: `tests/test_catalog_write_sink.py::test_released_changes_apply_with_version_check`.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R003.1`: planned proof `tests/test_catalog_write_sink.py::test_released_changes_apply_with_version_check`. Expected: A released create and a released update each make one store call.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R003.2`: planned proof `tests/test_catalog_write_sink.py::test_version_conflict_refuses_without_write`. Expected: A version conflict makes no write call.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R003.3`: planned proof `tests/test_catalog_write_sink.py::test_registered_sink_round_trips_version`. Expected: The read-back version is one higher.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004`: planned proof `tests/test_egeria_63_contract.py::test_tools_round_trip_against_the_63_type_system`. Expected: Rollup closes when `.1` to `.3` are verified.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.1`: planned proof `tests/test_egeria_63_contract.py::test_tools_round_trip_against_the_63_type_system`. Expected: Recorded 6.3 fixtures round-trip; a removed type yields `UNSUPPORTED_TYPE`.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.2`: planned proof `tests/test_egeria_63_contract.py::test_older_platform_refuses_writes_and_names_versions`. Expected: A 5.x platform refuses writes with `PLATFORM_VERSION_UNSUPPORTED` and makes no write call.
- `CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.3`: planned proof `tests/test_egeria_63_contract.py::test_docs_name_no_5x_platform`. Expected: No `egeria-platform:5.` reference remains in docs.
