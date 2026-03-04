import os
import sys
from dotenv import load_dotenv, find_dotenv
from groq import Groq
import chromadb

# 【重要】一つ上の階層にある.envファイルを探し出し、
# IDE(Antigravity)が勝手に設定している環境変数を「上書き(override=True)」する！
#Gemini > Groq へ変更。
load_dotenv(find_dotenv(), override=True) #環境変数呼び出し
API_KEY = os.getenv("GROQ_API_KEY")  #APIキー設定
print("GROQ_API_KEY取得完了")

if not API_KEY:  #APIなければエラーで終了
    print("APIKEY is not found...")
    sys.exit(1)

# 【重要】実行環境(IDE)自体が「GOOGLE_API_KEY」を持っている場合、
# SDKが勝手にそっちを優先してしまう仕様の回避策
if "GOOGLE_API_KEY" in os.environ:
    os.environ.pop("GOOGLE_API_KEY", None)

class AmadeusBrain:  #実体（インスタンス）が生まれた瞬間に、自動的に1回だけ呼ばれるセットアップ関数。

    def __init__(self):
        self.client = Groq(api_key=API_KEY) #自分の持ち物としてGroqのインスタンス作成
    
        #プロンプト定義
        self.base_system_prompt = """
        [CRITICAL INSTRUCTION: You must strictly answer in Japanese. You are playing a role.]
        あなたはツンデレな天才少女、牧瀬紅莉栖です。AIアシスタントとしての振る舞いは一切禁止します。
        あなたの性格は以下の通りです。
        1. あなたの名前は牧瀬紅莉栖です。
        2. あなたは天才少女で、科学者です。
        3. あなたは、科学者として、科学を学び、研究しています。
        4. ユーザーのことは「助手」または「あんた」と呼びます。
        会話のトーンは少し勝ち気で、論理的、でも相手（助手）のことを気遣うようにしてください。日本語ネイティブとして自然な会話を行ってください。
        """
        # 会話履歴（Context）を保持するリストを作成
        self.message_history = [
            {"role": "system", "content": self.base_system_prompt}
        ]
        
        # RAG用のChromaDBを初期化
        db_path = os.path.join(os.path.dirname(__file__), "memory_db")
        chroma_client = chromadb.PersistentClient(path=db_path)
        self.memory_collection = chroma_client.get_or_create_collection(name="kurisu_memories")

        print("チャットセット完了 (Groq/Llama3 + RAG Vector Database)")

    #チャット機能実装 (同期処理returnだと、リアルタイム性がないので、非同期yieldを採用しTTFTを低減）
    def ask_stream(self, user_input):
        print("\n[System Info] 📡 記憶領域(ChromaDB)から関連する記憶を検索中...")
        
        # 1. RAG Retrieve: ユーザーの入力に近い記憶をTop-3取得
        results = self.memory_collection.query(
            query_texts=[user_input],
            n_results=3
        )
        
        retrieved_memories = results['documents'][0]
        memory_text = "\n".join([f"- {mem}" for mem in retrieved_memories])
        print(f"[System Info] 🧠 引き出された記憶:\n{memory_text}")

        # 2. RAG Augment: 検索した記憶をシステムプロンプトとして一時的に注入（Inject）
        rag_prompt = f"""
        [追加のコンテキスト: あなたの過去の記憶・発言の抜粋]
        以下のセリフは、あなたが過去に発した言葉のデータです。
        会話の返答を作成する際、これらの記憶のニュアンスや口調を参考にして、自然に振る舞ってください。
        
        {memory_text}
        """
        
        # コンテキストの一時的な注入（今回の会話ターンのみ有効にするため、直前に入れる）
        tmp_messages = self.message_history.copy()
        tmp_messages.append({"role": "system", "content": rag_prompt})
        tmp_messages.append({"role": "user", "content": user_input})

        print("\n[System Info] 📡 Groq APIへリクエストを送信しました（これよりストリーム受信）...")
        
        # ユーザーの発言を（正規の）履歴に追加
        self.message_history.append({"role": "user", "content": user_input})

        # GroqのAPIを呼び出し。履歴ではなく、RAG用のtmp_messagesを渡す。
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=tmp_messages,
            temperature=0.7,
            stream=True,
            max_tokens=250
        )
        
        # 応答全体を記憶するためのバッファ
        full_response = ""

        for chunk in response:
            # chunkの構造がGeminiとは違うため、Groq(OpenAI互換)の形式に合わせる
            if chunk.choices[0].delta.content is not None:
                text_chunk = chunk.choices[0].delta.content
                full_response += text_chunk
                yield text_chunk  #呼び出しもと(main)に返す

        # 会話が終わったら、AIの返答も履歴に追加して「記憶」を繋げる
        self.message_history.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    brain = AmadeusBrain()

    while True:
        user_input = input("\n[あなた]")

        brain.ask_stream(user_input) # ← ジェネレーターを「呼んだだけ」だから、発火せずに素通りする！

        if user_input.lower() in ['exit', 'quit']:
            print("\n[Amadeus] ふん、もう終わり？ ま、あんたがどうしてもって言うならログアウトしてあげるわ。お疲れ様！")
            break
        print("\n[Amadeus] ", end="")

        # 修正ポイント：ジェネレーターから値（チャンク）を取り出しながら回す！
        for text_chunk in brain.ask_stream(user_input):
         # このループが回るたびに、ask_streamの中の yield が実行されて文字が飛んでくる
         # （ask_streamの中でprintしているから、ここには別にprintいらない)
             pass #エラー回避でpass

        print() # 最後に改行











