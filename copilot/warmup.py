"""Load models, the CSV frames, and the kNN index before the first timed request."""

from __future__ import annotations


def warmup() -> None:
    """Pay the cold-start cost once: frames, chunks, vectors, kNN, one encode, one rerank."""
    from copilot.agents.retrieval import _kb_matrix
    from copilot.data import load_frames
    from copilot.embed import encode, rerank
    from copilot.kb import load_chunks
    from copilot.knn import load_index

    load_frames()
    chunks = load_chunks()
    _kb_matrix(chunks)
    load_index()
    encode(["warmup"], for_retrieval=True)
    sample = chunks[0].text if chunks else "policy"
    rerank("warmup", [sample])
