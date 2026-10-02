"""Optional bounded process workers for the unchanged coupled-pose predicate.

The parent consumes results in manifest pose order, including errors. Workers
perform geometry only; they never launch another sweep or evaluate drive proof.
"""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pathlib import Path
import runpy
import tempfile
import time


class GeometryError(ValueError):
    def __init__(self, kind, detail):
        self.kind = kind
        self.detail = detail
        super().__init__(f'{kind}: {detail}')


_STATE = None


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
    with tempfile.TemporaryDirectory(prefix='motion-brep-') as directory:
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
                executor.terminate_workers()
                # terminate_workers intentionally uses shutdown(wait=False).
                # Reap before deleting files an initializing worker might read.
                for process in processes:
                    try:
                        process.join(timeout=2)
                        if process.is_alive():
                            process.kill()
                            process.join(timeout=2)
                        if process.is_alive():
                            raise RuntimeError('motion worker did not terminate')
                    except ValueError:
                        # The executor management thread already reaped/closed it.
                        pass
