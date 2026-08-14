import json
import unittest
from unittest.mock import MagicMock

from aistore.mcp.tools.jobs import register_job_tools


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


class TestJobsTools(unittest.TestCase):
    def _make_tools(self, client):
        mcp = _CaptureMCP()
        register_job_tools(mcp, lambda: client)
        return mcp.tools

    def test_list_jobs_handles_none_end_time(self):
        status = MagicMock()
        status.uuid = "job-1"
        status.err = None
        status.end_time = None
        status.aborted = False

        cluster = MagicMock()
        cluster.list_jobs_status.return_value = [status]
        client = MagicMock()
        client.cluster.return_value = cluster

        tools = self._make_tools(client)
        result = tools["ais_list_jobs"]()
        parsed = json.loads(result)
        self.assertEqual(parsed["count"], 1)
        self.assertFalse(parsed["jobs"][0]["finished"])
        self.assertFalse(parsed["jobs"][0]["aborted"])

    def test_job_status_handles_none_end_time(self):
        job = MagicMock()
        job_status = MagicMock()
        job_status.err = None
        job_status.end_time = None
        job_status.aborted = False
        job.status.return_value = job_status
        job.get_details.return_value.list_snapshots.return_value = []

        client = MagicMock()
        client.job.return_value = job

        tools = self._make_tools(client)
        result = tools["ais_job_status"]("job-1")
        parsed = json.loads(result)
        self.assertEqual(parsed["id"], "job-1")
        self.assertFalse(parsed["finished"])
