"""35 loose parts; default setup, or explicit before/after presentation state."""
import os
from rainward_lib import assembly
PRINTABLE = False

def gen_step():
    state=os.environ.get('RAINWARD_STATE','setup')
    if state not in ('setup','before','after'):
        raise ValueError('RAINWARD_STATE must be setup, before or after')
    return assembly(state)
