#
# Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
#
"""
Unit tests for pyaisloader PutGetMixedBenchmark.put_benchmark (no cluster
required; the bucket is mocked and __init__/setup is bypassed).

Regression coverage for two bugs:
- size-based mode (totalsize set, no duration) crashed unpacking three
  values from the single object returned by __put_benchmark_h
- objs_created recorded every uploaded object twice (the helper appended
  obj.name directly and again via stats.update())
"""

import unittest
from unittest.mock import Mock, PropertyMock, patch

from pyaisloader.benchmark import PutGetMixedBenchmark


def make_bench(minsize=1024, maxsize=1024):
    """Build a PutGetMixedBenchmark without cluster access (skip __init__)."""
    bench = PutGetMixedBenchmark.__new__(PutGetMixedBenchmark)
    bench.put_pct = 100
    bench.duration = None
    bench.totalsize = None
    bench.minsize = minsize
    bench.maxsize = maxsize
    bench.etl_name = None
    bench.etl_spec_type = None
    return bench


def mock_bucket():
    """Bucket mock whose object(name) returns objects exposing .name."""
    bucket = Mock()

    def _object(name):
        obj = Mock()
        obj.name = name
        return obj

    bucket.object.side_effect = _object
    return bucket


def run_put(bench, duration, totalsize):
    with patch.object(
        PutGetMixedBenchmark,
        "bucket",
        new_callable=PropertyMock,
        return_value=mock_bucket(),
    ):
        return bench.put_benchmark(duration, totalsize)


class TestPutBenchmarkSizeBased(unittest.TestCase):
    """Size-based mode: totalsize set, no duration."""

    def test_size_based_put_completes(self):
        """Must not raise ValueError: not enough values to unpack."""
        result, objs_created = run_put(make_bench(), duration=0, totalsize=4096)
        self.assertGreaterEqual(result["bytes"], 4096)
        self.assertGreater(result["ops"], 0)
        self.assertEqual(result["ops"], len(objs_created))
        self.assertEqual(len(objs_created), len(set(objs_created)))


class TestPutBenchmarkObjsCreated(unittest.TestCase):
    """objs_created must contain one entry per uploaded object."""

    def test_time_based_put_has_no_duplicate_objs(self):
        result, objs_created = run_put(make_bench(), duration=0.05, totalsize=0)
        self.assertGreater(result["ops"], 0)
        self.assertEqual(result["ops"], len(objs_created))
        self.assertEqual(len(objs_created), len(set(objs_created)))


if __name__ == "__main__":
    unittest.main()
