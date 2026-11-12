"""Apache Egeria open-metadata ontology contribution (CONCEPT:AU-KG.ontology.package-federation-migration).

Data-only subpackage: it carries ``egeria.ttl`` (the ``owl:Ontology``
``https://knuckles-team.github.io/ontology/connector/egeria`` module — open-metadata assets, glossaries and
governance relationships, importing the enterprise ontology) which the
scion-sdk hub federates in via the ``scion_sdk.ontology_providers``
entry-point. It holds no business logic and no heavy imports so the hub can
resolve it cheaply.
"""
