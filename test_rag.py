import sys
import os

# AmadeusSystemフォルダにパスを通す
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amadeus_core import AmadeusBrain

def test_rag():
    brain = AmadeusBrain()
    
    test_query = "ねえ紅莉栖、タイムリープマシンについて教えてよ"
    print(f"\n[あなた] {test_query}")
    print("[Amadeus] ", end="")
    
    # ストリームレスポンスを受け取る
    for chunk in brain.ask_stream(test_query):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    test_rag()
