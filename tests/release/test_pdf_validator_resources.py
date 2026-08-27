import runpy
import unittest
from pathlib import Path


VALIDATOR_PATH = (
    Path(__file__).resolve().parents[2]
    / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/pdf_validator.py"
)
VALIDATOR = runpy.run_path(str(VALIDATOR_PATH))


class FakeResource:
    RLIM_INFINITY = 2**63 - 1
    RLIMIT_AS = 1
    RLIMIT_DATA = 2
    RLIMIT_RSS = 3
    RLIMIT_CPU = 4
    RLIMIT_NOFILE = 5

    def __init__(self, limits=None, fail_on=()):
        unbounded = (self.RLIM_INFINITY, self.RLIM_INFINITY)
        self.limits = {
            self.RLIMIT_AS: unbounded,
            self.RLIMIT_DATA: unbounded,
            self.RLIMIT_RSS: unbounded,
            self.RLIMIT_CPU: unbounded,
            self.RLIMIT_NOFILE: unbounded,
        }
        self.limits.update(limits or {})
        self.fail_on = set(fail_on)
        self.set_calls = []

    def getrlimit(self, resource_id):
        return self.limits[resource_id]

    def setrlimit(self, resource_id, limit):
        if resource_id in self.fail_on:
            raise ValueError("unsupported limit")
        self.set_calls.append((resource_id, limit))
        self.limits[resource_id] = limit


class FakeSignal:
    SIGALRM = 14
    SIGXCPU = 24

    def __init__(self):
        self.handlers = []
        self.alarms = []

    def signal(self, signum, handler):
        self.handlers.append((signum, handler))

    def alarm(self, seconds):
        self.alarms.append(seconds)


class PdfValidatorResourceTest(unittest.TestCase):
    def _install(self, platform, resource):
        signals = FakeSignal()
        VALIDATOR["_install_resource_limits"](
            _platform=platform,
            _resource_module=resource,
            _signal_module=signals,
        )
        return signals

    def test_linux_installs_memory_cpu_file_and_wall_limits(self):
        resource = FakeResource()

        signals = self._install("linux", resource)

        self.assertEqual(
            [resource_id for resource_id, _limit in resource.set_calls],
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(
            resource.limits[1][0], VALIDATOR["MAX_LINUX_PROCESS_ADDRESS_BYTES"]
        )
        self.assertEqual(resource.limits[4][0], VALIDATOR["MAX_PROCESS_CPU_SECONDS"])
        self.assertEqual(resource.limits[5][0], 64)
        self.assertEqual([signum for signum, _handler in signals.handlers], [14, 24])
        self.assertEqual(signals.alarms, [VALIDATOR["MAX_PROCESS_WALL_SECONDS"]])

    def test_darwin_skips_only_unbounded_address_family_limits(self):
        resource = FakeResource()

        self._install("darwin", resource)

        self.assertEqual(
            [resource_id for resource_id, _limit in resource.set_calls],
            [resource.RLIMIT_CPU, resource.RLIMIT_NOFILE],
        )

    def test_darwin_tightens_finite_inherited_memory_limit(self):
        inherited_limit = VALIDATOR["MAX_DARWIN_PROCESS_ADDRESS_BYTES"] // 2
        resource = FakeResource(
            limits={
                FakeResource.RLIMIT_AS: (
                    inherited_limit,
                    FakeResource.RLIM_INFINITY,
                ),
            }
        )

        self._install("darwin", resource)

        self.assertIn(
            (
                resource.RLIMIT_AS,
                (inherited_limit, resource.RLIM_INFINITY),
            ),
            resource.set_calls,
        )

    def test_linux_requires_address_space_capability(self):
        resource = FakeResource()
        resource.RLIMIT_AS = None

        with self.assertRaisesRegex(
            VALIDATOR["PdfRejected"],
            "requires RLIMIT_AS process resource limits",
        ):
            self._install("linux", resource)

    def test_resource_limit_failure_is_not_silently_ignored(self):
        resource = FakeResource(fail_on=(FakeResource.RLIMIT_CPU,))

        with self.assertRaisesRegex(
            VALIDATOR["PdfRejected"],
            "could not install RLIMIT_CPU process resource limit",
        ):
            self._install("darwin", resource)

    def test_unknown_platform_fails_closed_before_installing_limits(self):
        resource = FakeResource()

        with self.assertRaisesRegex(
            VALIDATOR["PdfRejected"],
            "unsupported PDF validation platform: win32",
        ):
            self._install("win32", resource)

        self.assertEqual(resource.set_calls, [])


if __name__ == "__main__":
    unittest.main()
