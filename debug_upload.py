"""
Simulate show_upload() rendering without a real Streamlit context.
Patches all st.* calls to no-ops so we can trace what actually crashes.
"""
import sys
import traceback

# Mock streamlit
class MockSt:
    session_state = {}
    def __getattr__(self, name):
        def noop(*a, **kw):
            # Return something useful for specific calls
            if name == 'columns':
                n = a[0] if a else 2
                count = n if isinstance(n, int) else len(n)
                return [MockSt() for _ in range(count)]
            if name in ('file_uploader',):
                return []  # No files uploaded
            if name in ('number_input',):
                return 1
            if name in ('selectbox',):
                return a[1][0] if (len(a) > 1 and isinstance(a[1], list)) else 'Black & White'
            if name in ('toggle',):
                return False
            if name in ('container',):
                return MockContext()
            return None
        return noop
    def __enter__(self): return self
    def __exit__(self, *a): pass

class MockContext:
    def __enter__(self): return MockSt()
    def __exit__(self, *a): pass

mock_st = MockSt()
sys.modules['streamlit'] = mock_st

# Now try to run show_upload
try:
    # Re-import after mocking
    import importlib
    if 'smartviews.upload' in sys.modules:
        del sys.modules['smartviews.upload']
    # Also remove cached sub-modules
    for k in list(sys.modules.keys()):
        if 'smartai' in k or 'smartdb' in k or 'smartutils' in k:
            del sys.modules[k]
    
    # Now import with real modules but mocked streamlit
    mod = importlib.import_module('smartviews.upload')
    print("Module imported OK")
    
    # Try calling show_upload
    mock_st.session_state = {'user': {'id': 1, 'username': 'student'}}
    mod.show_upload()
    print("show_upload() completed OK")
    
except Exception as e:
    print(f"\n{'='*60}")
    print(f"EXCEPTION: {type(e).__name__}: {e}")
    print(f"{'='*60}")
    traceback.print_exc()
