from enum import Enum
from typing import Set

from weaviate.collections.classes.config import (
    DataType, Property, Configure, Tokenization
)
from weaviate.collections.classes.config_vectorizers import VectorDistances

from app.weaviate.client import get_client


class RequestContextSchema(Enum):
    COLLECTION_NAME = "ProcurementRequestContext"
    REQUEST_ID = "requestId"
    COMMODITY_GROUP = "commodityGroup"
    EMBEDDED_REQUEST_CONTEXT = "embeddedRequestContext"


def ensure_schema() -> None:
    """
    Idempotent schema creation for the commodity-group mapping store.
    Manual vectors (vectorizer=None), HNSW+COSINE, minimal inverted index.
    """
    client = get_client()
    name = RequestContextSchema.COLLECTION_NAME.value

    if client.collections.exists(name):
        _ensure_properties()
        return

    props = [
        Property(
            name=RequestContextSchema.REQUEST_ID.value,
            description="ID in relational DB as string",
            data_type=DataType.TEXT,
            index_filterable=True,
            index_searchable=False,
            tokenization=Tokenization.FIELD,
        ),
        Property(
            name=RequestContextSchema.COMMODITY_GROUP.value,
            description="Assigned commodity group label",
            data_type=DataType.TEXT,
            index_filterable=True,
            index_searchable=False,
            tokenization=Tokenization.FIELD,
        ),
        Property(
            name=RequestContextSchema.EMBEDDED_REQUEST_CONTEXT.value,
            description="Raw textual context used for embedding (title, vendor, lines…)",
            data_type=DataType.TEXT,
            index_inverted=False,
        ),
    ]

    vector_index = Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE)
    inverted_idx = Configure.inverted_index(index_property_length=True)

    client.collections.create(
        name=name,
        description="Commodity-group mapping store for finalized procurement requests",
        properties=props,
        vector_index_config=vector_index,
        vectorizer_config=None,         # manual vectors
        inverted_index_config=inverted_idx,
    )


def _ensure_properties() -> None:
    """
    If you later add props, this keeps backward compatibility by adding missing ones.
    """
    client = get_client()
    col = client.collections.get(RequestContextSchema.COLLECTION_NAME.value)

    cfg = col.config.get()
    existing: Set[str] = {p.name for p in (cfg.properties or [])}

    desired = {
        RequestContextSchema.REQUEST_ID.value: Property(
            name=RequestContextSchema.REQUEST_ID.value,
            description="ID in relational DB as string",
            data_type=DataType.TEXT,
            index_filterable=True,
            index_searchable=False,
            tokenization=Tokenization.FIELD,
        ),
        RequestContextSchema.COMMODITY_GROUP.value: Property(
            name=RequestContextSchema.COMMODITY_GROUP.value,
            description="Assigned commodity group label",
            data_type=DataType.TEXT,
            index_filterable=True,
            index_searchable=False,
            tokenization=Tokenization.FIELD,
        ),
        RequestContextSchema.EMBEDDED_REQUEST_CONTEXT.value: Property(
            name=RequestContextSchema.EMBEDDED_REQUEST_CONTEXT.value,
            description="Raw textual context used for embedding (title, vendor, lines…)",
            data_type=DataType.TEXT,
            index_inverted=False,
        ),
    }

    for key, prop in desired.items():
        if key not in existing:
            col.config.add_property(prop)