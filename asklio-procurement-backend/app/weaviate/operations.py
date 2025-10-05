from typing import Optional, List, Dict
from weaviate.collections import Collection
from weaviate.collections.classes.filters import Filter
import weaviate.classes as wvc

from app.weaviate.client import get_client
from app.weaviate.bootstrap import RequestContextSchema, ensure_schema


def _collection() -> Collection:
    ensure_schema()
    return get_client().collections.get(RequestContextSchema.COLLECTION_NAME.value)


def add(
    request_id: int | str,
    commodity_group: str,
    embedded_request_context: str,
    vector: Optional[List[float]] = None,
) -> str:
    """
    Insert one object. If you already computed an embedding, pass it as 'vector'.
    Returns the inserted UUID.
    """
    col = _collection()
    props = {
        RequestContextSchema.REQUEST_ID.value: str(request_id),
        RequestContextSchema.COMMODITY_GROUP.value: commodity_group,
        RequestContextSchema.EMBEDDED_REQUEST_CONTEXT.value: embedded_request_context,
    }
    if vector is not None:
        return col.data.insert(properties=props, vector=vector)
    return col.data.insert(properties=props)


def delete(request_id: int | str) -> None:
    """
    Delete all objects for a given request id.
    """
    col = _collection()
    col.data.delete_many(
        where=Filter.by_property(RequestContextSchema.REQUEST_ID.value).equal(str(request_id))
    )


def update_commodity_group(request_id: int | str, new_commodity_group: str) -> int:
    """
    Update the commodityGroup for all objects matching the given request id.
    Returns the number of updated objects.
    """
    col = _collection()
    results = col.query.fetch_objects(
        filters=Filter.by_property(RequestContextSchema.REQUEST_ID.value).equal(str(request_id))
    )
    if not results.objects:
        return 0

    updated = 0
    for obj in results.objects:
        col.data.update(
            uuid=obj.uuid,
            properties={RequestContextSchema.COMMODITY_GROUP.value: new_commodity_group},
        )
        updated += 1
    return updated

def search_similar(
    vector: List[float],
    top_k: int = 10,
    commodity_group_id: Optional[str] = None,
) -> List[Dict]:
    """
    Vector similarity search over ProcurementRequestContext.
    Optionally filter by `commodity_group_id`.
    Returns a list of dicts with properties + metadata (certainty/score/distance/uuid).
    """
    col = _collection()

    filters = None
    if commodity_group_id:
        filters = Filter.by_property(RequestContextSchema.COMMODITY_GROUP.value).equal(commodity_group_id)

    res = col.query.near_vector(
        near_vector=vector,
        limit=top_k,
        filters=filters,
        return_metadata=wvc.query.MetadataQuery(certainty=True, score=True, distance=True),
    )

    out: List[Dict] = []
    for obj in res.objects:
        props = obj.properties or {}
        out.append({
            "uuid": obj.uuid,
            "requestId": props.get(RequestContextSchema.REQUEST_ID.value),
            "commodityGroup": props.get(RequestContextSchema.COMMODITY_GROUP.value),
            "embeddedRequestContext": props.get(RequestContextSchema.EMBEDDED_REQUEST_CONTEXT.value),
            "certainty": getattr(obj.metadata, "certainty", None),
            "score": getattr(obj.metadata, "score", None),
            "distance": getattr(obj.metadata, "distance", None),
        })
    return out