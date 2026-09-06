from typing import Any

def merge_messages(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Preserve previous messages, append new messages, deduplicate by ID if present."""
    existing_list = existing or []
    new_list = new or []
    seen_ids = set()
    merged = []
    
    for item in existing_list + new_list:
        item_id = getattr(item, 'id', None) or (item.get('id') if isinstance(item, dict) else None)
        if item_id:
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                merged.append(item)
        else:
            merged.append(item)
    return merged


def merge_documents(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Append new documents while avoiding duplicates based on document_id."""
    existing_list = existing or []
    new_list = new or []
    seen_ids = set()
    merged = []

    for doc in existing_list + new_list:
        doc_id = getattr(doc, 'document_id', None) or (doc.get('document_id') if isinstance(doc, dict) else None)
        if doc_id:
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(doc)
        else:
            merged.append(doc)
    return merged


def merge_insights(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Merge financial insights, updating confidence if a higher-confidence value arrives."""
    existing_list = existing or []
    new_list = new or []
    insight_map = {}

    for insight in existing_list + new_list:
        field_name = getattr(insight, 'field_name', None) or (insight.get('field_name') if isinstance(insight, dict) else None)
        confidence = getattr(insight, 'confidence', 0.0) or (insight.get('confidence', 0.0) if isinstance(insight, dict) else 0.0)

        if not field_name:
            continue

        if field_name not in insight_map:
            insight_map[field_name] = insight
        else:
            existing_conf = getattr(insight_map[field_name], 'confidence', 0.0) or (
                insight_map[field_name].get('confidence', 0.0) if isinstance(insight_map[field_name], dict) else 0.0
            )
            if confidence >= existing_conf:
                insight_map[field_name] = insight

    return list(insight_map.values())


def merge_routing_decisions(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Preserve audit log of all routing decisions in sequence."""
    existing_list = existing or []
    new_list = new or []
    return existing_list + new_list


def merge_context(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Merge retrieved context chunks, deduplicating by chunk_id."""
    existing_list = existing or []
    new_list = new or []
    seen_chunks = set()
    merged = []

    for ctx in existing_list + new_list:
        chunk_id = getattr(ctx, 'chunk_id', None) or (ctx.get('chunk_id') if isinstance(ctx, dict) else None)
        if chunk_id:
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                merged.append(ctx)
        else:
            merged.append(ctx)
    return merged


def merge_errors(existing: list[Any] | None, new: list[Any] | None) -> list[Any]:
    """Accumulate workflow errors for diagnostics."""
    existing_list = existing or []
    new_list = new or []
    return existing_list + new_list
