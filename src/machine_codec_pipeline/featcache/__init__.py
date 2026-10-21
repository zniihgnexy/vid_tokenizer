"""E-04 feature-cache compression baselines (MASTER_PLAN §3.1, D-006/D-013).

The competitor to a per-video INR codec is "just cache the VLM's visual tokens".
This package implements zero-training compressors for the frozen InternVL token
cache ([T, 256, 4096] per 128-frame chunk) so their bits can be put on the same
bpp axis as the codec (bits / (T * 256 * 256)):

  pool  - spatial average-pool to K tokens/frame (same op the QA path uses)
  pca   - shared basis fitted on donor videos (amortised, like the frozen adapter)
  sq    - uniform scalar quantiser with donor-fitted per-dimension ranges
  pq    - product quantiser with donor-fitted codebooks
  dpcm  - closed-loop temporal prediction in coefficient space
  bits  - order-0 entropy (ideal adaptive coder) and actual lzma size

Specs are strings such as ``p16_pca64_q4_t`` (see :mod:`spec`).
"""

from .spec import FeatSpec, parse_spec  # noqa: F401
from .codec import FeatCodec, Payload, bpp_of, pool_tokens, book_key  # noqa: F401
