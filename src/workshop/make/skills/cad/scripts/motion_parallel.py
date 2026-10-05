"""Optional bounded process workers for the unchanged coupled-pose predicate.

The parent consumes results in manifest pose order, including errors. Workers
perform geometry only; they never launch another sweep or evaluate drive proof.
"""
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
import multiprocessing
from pathlib import Path
import runpy
import shutil
import sys
import tempfile
import time


class GeometryError(ValueError):
    def __init__(self, kind, detail):
        self.kind = kind
        self.detail = detail
        super().__init__(f'{kind}: {detail}')


_STATE = None


@contextmanager
def _scratch_directory():
    """Cleanup is housekeeping, never a replacement geometry verdict.

    Native sandboxes may permit writing files but refuse directory removal.
    Preserve the measured result/exception and leave the owned scratch path
    for later cleanup; do not retry with changed permissions or escalate.
    """
    directory = tempfile.mkdtemp(prefix='motion-brep-')
    try:
        yield directory
    finally:
        try:
            shutil.rmtree(directory)
        except OSError as error:
            print(f'check_motion: scratch cleanup deferred: {directory}: '
                  f'{type(error).__name__}: {error}', file=sys.stderr, flush=True)


def _write_shape(shape, path):
    from OCP.BinTools import BinTools
    if not BinTools.Write_s(shape.wrapped, str(path)):
        raise ValueError('motion worker could not serialize operand')


def _read_shape(path):
    from build123d import Compound
    from OCP.BinTools import BinTools
    from OCP.TopoDS import TopoDS_Shape
    wrapped = TopoDS_Shape()
    if not BinTools.Read_s(wrapped, str(path)) or wrapped.IsNull():
        raise ValueError('motion worker could not restore operand')
    return Compound(wrapped)


def _initialize(tool_path, movers, obstacles, steps, tolerance):
    global _STATE
    tool = runpy.run_path(tool_path)
    # Workshop #102: the worker's overlap Booleans run serially, as the
    # parent's do.
    cadgen_src = Path(__file__).resolve().parent / 'packages' / 'cadgen' / 'src'
    if cadgen_src.is_dir() and str(cadgen_src) not in sys.path:
        sys.path.insert(0, str(cadgen_src))
    from cadgen.booleans import serial_booleans

    serial_booleans()
    placed = [(name, _read_shape(path), tool['_pose_table'](spec, steps, f'movers[{i}]'))
              for i, (name, path, spec) in enumerate(movers)]
    fixed = [(name, _read_shape(path)) for name, path in obstacles]
    scope = tool['validation_scope']()
    scope.__enter__()
    _STATE = tool, placed, fixed, steps, tolerance, scope


def _pose(step):
    tool, placed, obstacles, steps, tolerance, _scope = _STATE
    try:
        with tool['validation_scope'](), tool['decision_scope'](tolerance):
            posed = [(name, place(shape, step)) for name, shape, place in placed]
            for pair in range(len(posed)):
                others = posed[pair + 1:] + obstacles
                for other_name, other_shape in others:
                    volume = tool['overlap_volume'](posed[pair][1], other_shape)
                    if volume > tolerance:
                        return {'hit': {'step': step, 'steps': steps,
                                        'between': [posed[pair][0], other_name],
                                        'overlapMm3': round(volume, 6)}}
        return {'hit': None}
    except Exception as error:
        return {'error': (type(error).__name__, str(error))}


def sweep(tool_path, placed_shapes_specs, obstacles, steps, first, tol,
          workers, absolute_deadline, on_advance):
    """Return the first ordered collision or None; incomplete work raises.

    ``absolute_deadline`` is a monotonic timestamp or None. At most 2 * workers
    poses are in flight; their complete results are consumed in sample order.
    Binary OCCT persistence preserves B-reps without mesh approximation.
    Requires Python's explicit worker termination API for bounded cancellation.
    """
    if not hasattr(ProcessPoolExecutor, 'terminate_workers'):
        raise RuntimeError('parallel motion requires Python 3.14 worker termination')
    if workers < 1:
        raise ValueError('motion worker count must be positive')

    def remaining():
        if absolute_deadline is None:
            return None
        left = absolute_deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError('parallel coupled motion deadline reached')
        return left

    remaining()
    with _scratch_directory() as directory:
        root = Path(directory)
        movers = []
        fixed = []
        for index, (name, shape, spec) in enumerate(placed_shapes_specs):
            path = root / f'mover-{index}.brep'
            _write_shape(shape, path)
            movers.append((name, str(path), spec))
        for index, (name, shape) in enumerate(obstacles):
            path = root / f'obstacle-{index}.brep'
            _write_shape(shape, path)
            fixed.append((name, str(path)))
        remaining()
        executor = ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context('spawn'),
            initializer=_initialize,
            initargs=(str(tool_path), movers, fixed, steps, tol))
        completed = False
        futures = {}
        next_step = first
        try:
            for step in range(first, steps + 1):
                remaining()
                while next_step <= steps and len(futures) < workers * 2:
                    futures[next_step] = executor.submit(_pose, next_step)
                    next_step += 1
                result = futures.pop(step).result(timeout=remaining())
                remaining()
                if 'error' in result:
                    raise GeometryError(*result['error'])
                if result['hit'] is not None:
                    return result['hit']
                on_advance()
            completed = True
            return None
        finally:
            if completed:
                executor.shutdown(wait=True, cancel_futures=True)
            else:
                # A normal executor context waits for outstanding CAD operations
                # even after a collision/deadline. Terminate them explicitly.
                processes = list((getattr(executor, '_processes', None) or {}).values())
                manager = getattr(executor, '_executor_manager_thread', None)
                executor.terminate_workers()
                # The manager owns waitpid/reaping. Joining the same Process
                # concurrently can race its poll state and falsely report a
                # surviving worker. Wait for the owner, escalating signals only
                # if a native operation refuses termination.
                if manager is not None:
                    manager.join(timeout=2)
                    if manager.is_alive():
                        for process in processes:
                            try:
                                process.kill()
                            except (ValueError, ProcessLookupError):
                                pass
                        manager.join(timeout=2)
                    if manager.is_alive():
                        raise RuntimeError('motion worker manager did not terminate')
                else:
                    for process in processes:
                        process.join(timeout=2)
                        if process.is_alive():
                            process.kill()
                            process.join(timeout=2)
                        if process.is_alive():
                            raise RuntimeError('motion worker did not terminate')
