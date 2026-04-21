from store.store import Store
from models.types import AppState

def test_store():
    store = Store()
    captured_cpu = None
    
    def on_change(state):
        nonlocal captured_cpu
        captured_cpu = state.system.cpu
        print(f"CPU: {state.system.cpu}")
    
    store.subscribe(on_change)
    store.state.system.cpu = 45.5
    store.set_state(store.state)
    
    assert captured_cpu == 45.5, f"Expected 45.5, got {captured_cpu}"
    print("Store test passed!")

if __name__ == "__main__":
    test_store()